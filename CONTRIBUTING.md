# Contributing

**Adding new data**

+ For new products, copy the template from `templates/product.yml` into `data`. 
+ Give it a name in the format of `<brand>_<product>.yml`. 
	+ If you are adding data for an existing product but in different packaging, name it `<brand>_<product>_<packaging>.yml`.
+ Edit the file and submit your changes via a pull request. Please also send your source (URL, picture of beverage) for me to verify the data.

**Changing existing data**

+ Existing products can be found under `data`. 
+ Edit the file and submit your changes via a pull request. Please also send your source (URL, picture of beverage) for me to verify the data.

**Removing/Discontinuing a product**

+ Since this data should be a sort of archive, products should not get fully deleted
+ If a product is no longer available, set `discontinued` to `true` but **do not remove store links**
+ Edit the file and submit your changes via a pull request. Please also send your source (URL, picture of beverage) for me to verify the data.

## Missing data

| Product                  | Data     | Comment                                                |
|--------------------------|----------|--------------------------------------------------------|
| all i need mate tea      | Caffeine |                                                        |
| Coop Karma Mate & Orange | Caffeine |                                                        |
| Outlawz Holunder Mate    | Caffeine | Needs manual testing; manufacturer did not measure it  |
| Pri Mate                 | Caffeine |                                                        |