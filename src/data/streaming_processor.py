"""Streaming data processor for handling large CSV files."""

import logging
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

from ..config.constants import get_settings
from ..exceptions import (
    CSVProcessingError,
    FileProcessingError,
)

logger = logging.getLogger(__name__)


class StreamingCSVProcessor:
    """Process large CSV files in chunks to avoid memory issues."""

    def __init__(self, chunk_size: int = None):
        """
        Initialize the streaming processor.

        Args:
            chunk_size: Size of chunks to process (rows)
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.processing_limits.csv_chunk_size

    def read_csv_chunks(self, file_path: str) -> Iterator[pd.DataFrame]:
        """
        Read CSV file in chunks.

        Args:
            file_path: Path to CSV file

        Yields:
            DataFrame chunks

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large or invalid
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Check file size
        settings = get_settings()
        file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.processing_limits.max_file_size_mb:
            logger.warning(
                f"Large file detected: {file_size_mb:.1f}MB. "
                f"Using chunked processing with chunks of {self.chunk_size} rows."
            )

        try:
            chunk_count = 0
            total_rows = 0

            for chunk in pd.read_csv(file_path, chunksize=self.chunk_size):
                chunk_count += 1
                total_rows += len(chunk)

                logger.debug(f"Processing chunk {chunk_count} with {len(chunk)} rows")
                yield chunk

            logger.info(f"Processed {total_rows} total rows in {chunk_count} chunks")

        except pd.errors.EmptyDataError:
            logger.warning(f"Empty CSV file: {file_path}")
            return
        except pd.errors.ParserError as e:
            raise CSVProcessingError(
                f"Invalid CSV format in {file_path}: {e}", file_path=str(file_path)
            )
        except MemoryError as e:
            raise FileProcessingError(
                f"Insufficient memory to process {file_path}",
                file_path=str(file_path),
                file_type="CSV",
                operation="read_chunks",
            ) from e
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            raise FileProcessingError(
                f"Failed to read CSV file: {str(e)}",
                file_path=str(file_path),
                file_type="CSV",
                operation="read_chunks",
            ) from e

    def process_csv_with_callback(
        self, file_path: str, process_chunk_callback: callable, progress_callback: callable = None
    ) -> list[Any]:
        """
        Process CSV file with a callback function applied to each chunk.

        Args:
            file_path: Path to CSV file
            process_chunk_callback: Function to process each chunk
            progress_callback: Optional progress callback

        Returns:
            List of results from processing each chunk
        """
        results = []

        try:
            for chunk_num, chunk in enumerate(self.read_csv_chunks(file_path)):
                try:
                    chunk_result = process_chunk_callback(chunk)
                    if chunk_result is not None:
                        if isinstance(chunk_result, list):
                            results.extend(chunk_result)
                        else:
                            results.append(chunk_result)

                    if progress_callback:
                        progress_callback(chunk_num + 1, len(chunk))

                except (CSVProcessingError, FileProcessingError):
                    # Re-raise specific processing errors
                    raise
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_num}: {e}")
                    continue

        except (CSVProcessingError, FileProcessingError):
            # Re-raise specific processing errors
            raise
        except Exception as e:
            logger.error(f"Failed to process CSV file {file_path}: {e}")
            raise FileProcessingError(
                f"CSV processing failed: {str(e)}",
                file_path=file_path,
                file_type="CSV",
                operation="process_with_callback",
            ) from e

        return results

    def estimate_total_rows(self, file_path: str) -> int:
        """
        Estimate total number of rows in CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            Estimated row count
        """
        try:
            # Read first chunk to get column info
            first_chunk = next(self.read_csv_chunks(file_path))

            # Estimate total rows based on file size and first chunk
            file_size = Path(file_path).stat().st_size
            chunk_size_bytes = len(str(first_chunk))
            estimated_rows = int(file_size / chunk_size_bytes * len(first_chunk))

            logger.debug(f"Estimated {estimated_rows} rows in {file_path}")
            return estimated_rows

        except (CSVProcessingError, FileProcessingError) as e:
            logger.warning(f"Could not estimate row count for {file_path}: {e}")
            return -1
        except Exception as e:
            logger.warning(f"Unexpected error estimating row count for {file_path}: {e}")
            return -1

    def get_column_info(self, file_path: str) -> dict[str, Any]:
        """
        Get column information from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            Dictionary with column information
        """
        try:
            first_chunk = next(self.read_csv_chunks(file_path))

            return {
                "columns": list(first_chunk.columns),
                "column_count": len(first_chunk.columns),
                "dtypes": first_chunk.dtypes.to_dict(),
                "sample_row_count": len(first_chunk),
            }

        except (CSVProcessingError, FileProcessingError) as e:
            logger.error(f"Could not get column info for {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting column info for {file_path}: {e}")
            return {}

    def validate_csv_structure(self, file_path: str, expected_columns: list[str] = None) -> bool:
        """
        Validate CSV file structure.

        Args:
            file_path: Path to CSV file
            expected_columns: Expected column names

        Returns:
            True if structure is valid
        """
        try:
            column_info = self.get_column_info(file_path)

            if not column_info:
                return False

            columns = column_info["columns"]

            if expected_columns:
                missing_columns = set(expected_columns) - set(columns)
                if missing_columns:
                    logger.error(f"Missing expected columns in {file_path}: {missing_columns}")
                    return False

            logger.debug(f"CSV structure validated for {file_path}: {len(columns)} columns")
            return True

        except (CSVProcessingError, FileProcessingError) as e:
            logger.error(f"CSV structure validation failed for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating CSV structure for {file_path}: {e}")
            return False
