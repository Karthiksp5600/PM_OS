from pathlib import Path

from productpilot.discovery.connectors.kaggle_myntra import load_myntra_kaggle_connectors


def test_loads_myntra_app_reviews_from_local_json(tmp_path: Path):
    base_dir = tmp_path
    kaggle_dir = base_dir / "productpilot" / "discovery" / "data" / "kaggle_myntra"
    kaggle_dir.mkdir(parents=True)
    dataset_path = kaggle_dir / "Myntra.json"
    dataset_path.write_text(
        '[{"userName":"Asha","content":"Wishlist is too crowded so I forget saved items.","score":2,"thumbsUpCount":3,"at":"2026-08-24T12:42:51Z"}]',
        encoding="utf-8",
    )

    connectors = load_myntra_kaggle_connectors(base_dir)

    assert any(connector.source_name == "kaggle_myntra_app_reviews" for connector in connectors)
    connector = next(connector for connector in connectors if connector.source_name == "kaggle_myntra_app_reviews")
    records = connector.fetch()

    assert len(records) == 1
    assert "Wishlist is too crowded" in records[0].text
    assert records[0].rating == 2.0
    assert records[0].upvotes_likes == 3


def test_loads_only_present_myntra_kaggle_connectors(tmp_path: Path):
    base_dir = tmp_path
    kaggle_dir = base_dir / "productpilot" / "discovery" / "data" / "kaggle_myntra"
    kaggle_dir.mkdir(parents=True)
    dataset_path = kaggle_dir / "myntra-sales-dataset.csv"
    dataset_path.write_text(
        "Product Name,Brand,Price,Rating,Number of Ratings\n"
        "Myntra Kurta,Anouk,1299,4.3,120\n",
        encoding="utf-8",
    )

    connectors = load_myntra_kaggle_connectors(base_dir)

    assert len(connectors) == 1
    assert connectors[0].source_name == "kaggle_myntra_sales"

    records = connectors[0].fetch()
    assert len(records) == 1
    assert "Myntra Kurta" in records[0].text
