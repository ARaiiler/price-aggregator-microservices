"""
Inbound request models for the internal API.
"""
from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    """
    Payload accepted by POST /internal/search.

    This endpoint is intended exclusively for calls from the Node.js
    API Gateway.  No authentication is performed here — that
    responsibility belongs to the Gateway.
    """

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the product to search for",
        examples=["laptop", "wireless headphones"],
    )

    @field_validator("product_name")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("product_name must not be blank or whitespace-only")
        return stripped
