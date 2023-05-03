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
    return "{:.2f}".format(number)


def prepare_output_dir():
    # remove previously rendered pages
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    # create new dir
    os.mkdir(OUTPUT_DIR)
    os.mkdir(f"{OUTPUT_DIR}/products")

    # Copy over static assets
    for file in glob.iglob(f"{SCRIPT_DIR}/static/*"):
        shutil.copy(file, OUTPUT_DIR)


def render_products(env: jinja2.Environment, render_drafts: bool):
    print("[+] Rendering products")
    products = []
    product_template = env.get_template("product.jinja2")

    # process every ./products/product.yaml file
    for product_filepath in glob.iglob(f"{DATA_DIR}/*.yml"):
        # convert yaml to dict
        with open(product_filepath) as product_raw:
            product_yaml = yaml.safe_load(product_raw)

        if render_drafts is False and product_yaml.get("draft", False):
            print(
                f"[-] Skipping draft {product_yaml['brand']} {product_yaml['product']} ({product_yaml['packaging']})"
            )
            continue

        # if the draft flag on a file is set, add * to the beginning of the product name
        if product_yaml["draft"] == True:
            product_yaml.update({"product": (f"*{product_yaml['product']}")})

        # escape special chars from the filenames and
        # make lowercase to generate the url, ex. brand_product_packaging.html
        site_url = re.sub(
            r"[^a-zA-Z0-9\._]+",
            "_",
            f"{product_yaml['brand']}_{product_yaml['product']}_{product_yaml['packaging']}_{product_yaml['size']}.html",
        ).lower()
        # adding the "insite url" to product
        product_yaml.update({"siteurl": site_url})

        # average price
        product_prices = 0
        for store in product_yaml["stores"]:
            # add the price of one unit to the total
            product_price1u = store["price"] / store["amount"]  # single unit
            product_prices += product_price1u
            # add the price per one unit
            store.update({"price1u": round2(product_price1u)})
            # update value to be string with two decimal points
            store.update({"price": round2(store["price"])})

        product_averageprice = product_prices / len(product_yaml["stores"])
        # add average price to product
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
        # sugar can be zero
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

        # render product page brand_product_packaging.html
        with open(f"{OUTPUT_DIR}/products/{site_url}", "w") as product_out:
            product_out.write(product_template.render(item=product_yaml))

    print(f"[+] Rendererd {len(products)} products")
    return products


def render_index(env: jinja2.Environment, products: Iterable[Dict]):
    print("[+] Rendering 'index.html'")
    main_template = env.get_template("main.jinja2")
    # load all the contributors
    with open(f"{SCRIPT_DIR}/CONTRIBUTORS") as contributors_raw:
        contributors = contributors_raw.readlines()[1:]

    # render index.html
    with open(f"{OUTPUT_DIR}/index.html", "w") as main_out:
        main_out.write(
            main_template.render(
                products=products,
                contributors=contributors,
            )
        )


def render_more(env: jinja2.Environment, products: Iterable[Dict]):
    print("[+] Rendering 'more.html'")
    more_template = env.get_template("more.jinja2")
    with open(f"{OUTPUT_DIR}/more.html", "w") as more_out:
        more_out.write(more_template.render(products=products))


def render_sitemap(env: jinja2.Environment, urls: Iterable[str]):
    print("[+] Rendering 'sitemap.xml'")
    sitemap_template = env.get_template("sitemap.jinja2")
    with open(f"{OUTPUT_DIR}/sitemap.xml", "w") as sitemap_out:
        sitemap_out.write(
            sitemap_template.render(
                urls=sorted(urls),
                now=datetime.datetime.utcnow,
            ),
        )


def gather_sitemap_urls():
    return [
        "https://matelab.ch/" + fpath[len(OUTPUT_DIR)+1:]
        for fpath in sorted(glob.glob(f"{OUTPUT_DIR}/**/*.html", recursive=True))
    ]


def main(args):
    prepare_output_dir()
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(f"{SCRIPT_DIR}/templates/"))
    products = render_products(env, render_drafts=args.drafts)
    render_more(env, products)
    render_index(env, products)
    urls = gather_sitemap_urls()
    render_sitemap(env, urls=urls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--drafts", action="store_true")
    args = parser.parse_args()
    main(args)
