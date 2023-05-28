def get_request_headers() -> dict[str, str]:
    return {
        "User-Agent": """Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) \
                                AppleWebKit/537.36 (KHTML, like Gecko) \
                                Chrome/50.0.2661.102 Safari/537.36""",
    }


def get_s3_bucket_name() -> str:
    import os

    return os.environ.get("TF_VAR_NEWSWATCH_S3_BUCKET", "")


def get_extract_s3_prefix() -> str:
    return "extracted-headlines"


def get_sites_yaml_path() -> str:
    return "src/sites-with-filters.yaml"
