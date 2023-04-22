resource "aws_s3_bucket" "newswatch" {
  bucket = var.NEWSWATCH_S3_BUCKET
}

resource "aws_s3_bucket_public_access_block" "newswatch" {
  bucket = aws_s3_bucket.newswatch.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "newswatch" {
  bucket = aws_s3_bucket.newswatch.id
  versioning_configuration {
    status = "Enabled"
  }
}
