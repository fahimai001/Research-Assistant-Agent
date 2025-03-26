from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TopicRecommendation(BaseModel):
    """Schema for a single topic recommendation"""
    topic: str = Field(..., description="Name of the recommended topic")
    description: str = Field(..., description="Brief description of why this topic is relevant")
    resource_url: str = Field(..., description="URL for a relevant resource about this topic")

class TopicRecommendations(BaseModel):
    """Schema for a list of topic recommendations"""
    recommendations: List[TopicRecommendation] = Field(..., description="List of recommended topics")

class PaperRecommendation(BaseModel):
    """Schema for a single paper recommendation"""
    title: str = Field(..., description="Title of the recommended paper")
    authors: str = Field(..., description="Authors of the paper")
    year: str = Field(..., description="Publication year")
    description: str = Field(..., description="Brief description of why this paper is relevant")
    paper_url: str = Field(..., description="URL to access the paper")

class PaperRecommendations(BaseModel):
    """Schema for a list of paper recommendations"""
    recommendations: List[PaperRecommendation] = Field(..., description="List of recommended papers")

def define_output_schemas():
    """Return the Pydantic models for structured outputs"""
    return TopicRecommendations, PaperRecommendations