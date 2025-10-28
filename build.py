import os
import glob
import re
import argparse
import datetime
import shutil
from typing import Iterable, Dict

import yaml
import jinja2

# argument
SCRIPT_DIR = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
DATA_DIR = os.path.join(SCRIPT_DIR, "data")


def round2(number):
    """
    Rounds a number to two decimal places
    """
    return "{:.2f}".format(number)


def prepare_output_dir():
    """
    Removes old builds, creates the new directory and copies over all static assets
    """
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    os.mkdir(OUTPUT_DIR)
    os.mkdir(f"{OUTPUT_DIR}/products")

    for file in glob.iglob(f"{SCRIPT_DIR}/static/*"):
        shutil.copy(file, OUTPUT_DIR)


def render_products(env: jinja2.Environment, render_drafts: bool):
    """
    Renders all products in ./data to their individual pages
    """
    print("[+] Rendering products")
    products = []
    product_template = env.get_template("product.jinja2")

    # process every ./data/*.yaml/yml file
    product_filepaths = glob.glob(f"{DATA_DIR}/*.yml") + glob.glob(f"{DATA_DIR}/*.yaml")

    for product_filepath in product_filepaths:
        with open(product_filepath) as product_raw:
            product_yaml = yaml.safe_load(product_raw)

        if render_drafts is False and product_yaml.get("draft", False):
            print(
                f"[-] Skipping draft {product_yaml['brand']} {product_yaml['product']} ({product_yaml['packaging']})"
            )
            continue

        # escape special chars from the filenames and
        # make lowercase to generate the url, ex. brand_product_packaging.html
        site_url = re.sub(
            r"[^a-zA-Z0-9\._]+",
            "_",
            f"{product_yaml['brand']}_{product_yaml['product']}_{product_yaml['packaging']}_{product_yaml['size']}.html",
        ).lower()
        product_yaml.update({"siteurl": site_url})

        # average price
        product_prices = 0
        for store in product_yaml["stores"]:
            product_price1u = (
                store["price"] / store["amount"]
            )  # only take a single unit
            product_prices += product_price1u
            store.update({"price1u": round2(product_price1u)})
            store.update({"price": round2(store["price"])})

        newest_update = datetime.date(1970, 1, 1)
        for store in product_yaml["stores"]:
            if store["date"] > newest_update:
                newest_update = store["date"]
        product_yaml["newest_update"] = newest_update

        product_averageprice = product_prices / len(product_yaml["stores"])
        product_yaml.update({"averageprice": round2(product_averageprice)})

        # price100ml
        product_price100ml = (product_averageprice / product_yaml["size"]) * 100
        product_yaml.update({"price100ml": round2(product_price100ml)})

        # price1mgcaffeine
        product_price1mgcaffeine = product_averageprice / product_yaml["caffeine"]
        product_yaml.update({"price1mgcaffeine": round2(product_price1mgcaffeine)})

        # total caffein in product
        product_caffeinetotal = product_yaml["caffeine"] * (product_yaml["size"] / 100)
        product_yaml.update({"caffeinetotal": round2(product_caffeinetotal)})

        # Set defaults when sugar is 0
        product_yaml.update(
            {
                "sugar1mgcaffeine": "0",
                "caffeine1gsugar": "0",
                "sugartotal": "0",
            }
        )

        if product_yaml["sugar"] != 0:
            # sugar1mgcaffeine
            product_sugar1mgcaffeine = product_yaml["sugar"] / product_yaml["caffeine"]
            product_yaml.update({"sugar1mgcaffeine": round2(product_sugar1mgcaffeine)})

            # caffeine1gsugar
            product_caffeine1gsugar = product_yaml["caffeine"] / product_yaml["sugar"]
            product_yaml.update({"caffeine1gsugar": round2(product_caffeine1gsugar)})

            # total sugar in product
            product_sugartotal = product_yaml["sugar"] * (product_yaml["size"] / 100)
            product_yaml.update({"sugartotal": round2(product_sugartotal)})

        products.append(product_yaml)

        # add the filename to the struct for the "Open on GitHub" link
        product_yaml["filename"] = os.path.basename(product_filepath)

        # render product page brand_product_packaging.html
        with open(f"{OUTPUT_DIR}/products/{site_url}", "w") as product_out:
            product_out.write(
                product_template.render(
                    item=product_yaml,
                    now=datetime.datetime.utcnow,
                )
            )

    print(f"[+] Rendererd {len(products)} products")
    return products


def render_index(env: jinja2.Environment, products: Iterable[Dict]):
    """
    Renders the main/landing/index page
    """

    print("[+] Rendering 'index.html'")
    main_template = env.get_template("main.jinja2")

    with open(f"{OUTPUT_DIR}/index.html", "w") as main_out:
        main_out.write(
            main_template.render(
                products=products,
                now=datetime.datetime.utcnow,
            )
        )


def render_sitemap(env: jinja2.Environment, urls: Iterable[str]):
    """
    Renders the sitemap.xml
    """

    print("[+] Rendering 'sitemap.xml'")
    sitemap_template = env.get_template("sitemap.jinja2")
    with open(f"{OUTPUT_DIR}/sitemap.xml", "w") as sitemap_out:
        sitemap_out.write(
            sitemap_template.render(
                urls=sorted(urls),
                now=datetime.datetime.utcnow,
            ),
        )


def render_rss(env: jinja2.Environment, products: Iterable[Dict]):
    """
    Renders the RSS feed
    """

    print("[+] Rendering 'feed.xml'")
    rss_template = env.get_template("rss.jinja2")

    sorted_products = sorted(
        products, key=lambda product: product["newest_update"], reverse=True
    )

    with open(f"{OUTPUT_DIR}/feed.xml", "w") as rss_out:
        rss_out.write(
            rss_template.render(
                products=sorted_products,
                now=datetime.datetime.utcnow,
            )
        )


def gather_sitemap_urls():
    """
    Returns a array of URL to include in the sitemap.
    Called after rendering all other pages
    """

    return [
        "https://matelab.ch/" + fpath[len(OUTPUT_DIR) + 1 :]
        for fpath in sorted(glob.glob(f"{OUTPUT_DIR}/**/*.html", recursive=True))
    ]


def main(args):
    prepare_output_dir()

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(f"{SCRIPT_DIR}/templates/"))
    products = render_products(env, render_drafts=args.drafts)
    render_index(env, products)

    urls = gather_sitemap_urls()
    render_sitemap(env, urls=urls)
    render_rss(env, products)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--drafts", action="store_true")
    args = parser.parse_args()
    main(args)
