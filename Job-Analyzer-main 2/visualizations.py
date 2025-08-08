import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np

def create_skill_match_chart(job_skills, resume_skills):
    """Create a bar chart showing skills match percentage"""
    # Calculate the percentage of job skills found in resume
    if not job_skills:
        return None
        
    matched_skills = [skill for skill in job_skills if skill in resume_skills]
    match_percentage = (len(matched_skills) / len(job_skills)) * 100
    
    # Create a simple bar chart
    fig = go.Figure(go.Bar(
        x=['Skill Match'],
        y=[match_percentage],
        text=[f"{match_percentage:.1f}%"],
        textposition='auto',
        marker_color='royalblue'
    ))
    
    fig.update_layout(
        title="Resume-Job Skills Match",
        yaxis=dict(range=[0, 100], title="Match Percentage"),
        height=400
    )
    
    return fig

def create_skills_radar_chart(categories, job_scores, resume_scores):
    """Create a radar chart comparing job requirements vs. resume skills"""
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=job_scores,
        theta=categories,
        fill='toself',
        name='Job Requirements'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=resume_scores,
        theta=categories,
        fill='toself',
        name='Your Resume'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        title="Skills Gap Analysis",
        showlegend=True
    )
    
    return fig

def create_missing_skills_chart(missing_skills, category_mapping=None):
    """Create a horizontal bar chart of missing skills"""
    if not missing_skills:
        return None
        
    if category_mapping:
        # Group missing skills by category
        categories = []
        for skill in missing_skills:
            category = "Other"
            for cat, skills in category_mapping.items():
                if skill.lower() in [s.lower() for s in skills]:
                    category = cat
                    break
            categories.append(category)
        
        # Count skills by category
        df = pd.DataFrame({
            'Skill': missing_skills,
            'Category': categories
        })
        count_df = df['Category'].value_counts().reset_index()
        count_df.columns = ['Category', 'Count']
        
        fig = px.bar(count_df, x='Count', y='Category', orientation='h',
                     title='Missing Skills by Category')
    else:
        # Simple count of missing skills
        fig = px.bar(
            x=range(len(missing_skills)),
            y=missing_skills,
            orientation='h',
            title='Missing Skills from Your Resume'
        )
        fig.update_xaxes(title="")
        fig.update_yaxes(title="")
    
    return fig
