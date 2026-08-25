# Myntra-only Kaggle sources

Drop only the Myntra-specific Kaggle dataset exports into this folder using these filenames:

- `myntra-shopping-app-reviews.json`
  - Source: `https://www.kaggle.com/datasets/jocelyndumlao/shoppingappreviews-dataset`
  - You can also place the signed Kaggle/Google Storage URL into `myntra-shopping-app-reviews.url`
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
- `.jsonl`

The discovery pipeline will auto-detect any of these files and add them as optional Myntra-only sources.
