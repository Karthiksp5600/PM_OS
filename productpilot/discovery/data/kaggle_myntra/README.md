# Myntra-only Kaggle sources

The packaged `myntra-shopping-app-reviews.json.gz` file is the default local source for Myntra app reviews. It replaces the previous expiring signed download link.

Drop only the Myntra-specific Kaggle dataset exports into this folder using these filenames:

- `myntra-shopping-app-reviews.json.gz`
  - Source: `https://www.kaggle.com/datasets/jocelyndumlao/shoppingappreviews-dataset`
- `myntra-fashion-dataset.csv`
  - Source: `https://www.kaggle.com/datasets/manishmathias/myntra-fashion-dataset`
- `myntra-fashion-products.csv`
  - Source: `https://www.kaggle.com/datasets/nirokey/myntra-fashion-products`
- `myntra-sales-dataset.csv`
  - Source: `https://www.kaggle.com/datasets/skmewati/myntra-sales-dataset`
- `myntra-fashion-product-dataset.csv`
  - Source: `https://www.kaggle.com/datasets/djagatiya/myntra-fashion-product-dataset`
- `myntra-products-dataset.csv`
  - Source: `https://www.kaggle.com/datasets/ronakbokaria/myntra-products-dataset/versions/1`

Supported formats:

- `.csv`
- `.json`
- `.json.gz`
- `.jsonl`

The discovery pipeline will auto-detect any of these files and add them as optional Myntra-only sources.
