import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import io
import base64
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class DataVisualizer:
    def __init__(self):
        """Initialize the enhanced data visualizer with Plotly support"""
        # Set style for better-looking plots
        plt.style.use('default')
        sns.set_palette("husl")

        # Configure matplotlib for non-interactive backend
        plt.switch_backend('Agg')

        # Configure Plotly
        pio.templates.default = "plotly_white"

        # Color schemes for consistent styling
        self.color_schemes = {
            'primary': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'business': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#592E83'],
            'modern': ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51']
        }

        logger.info("Enhanced Data Visualizer initialized with Plotly support")
    
    def create_visualization(self, data: List[Dict[str, Any]], query: str, use_plotly: bool = True) -> Optional[str]:
        """
        Create an enhanced visualization based on the data and query

        Args:
            data: List of dictionaries containing the data
            query: Original query that generated the data
            use_plotly: Whether to use Plotly (interactive) or matplotlib (static)

        Returns:
            Base64 encoded image string or HTML string for Plotly charts
        """
        if not data:
            logger.warning("No data provided for visualization")
            return None

        try:
            # Convert data to pandas DataFrame
            df = pd.DataFrame(data)
            logger.info(f"Creating visualization for {len(df)} records")

            # Determine the best visualization type based on data and query
            viz_type = self._determine_visualization_type(df, query)
            logger.info(f"Selected visualization type: {viz_type}")

            if use_plotly:
                return self._create_plotly_chart(df, query, viz_type)
            else:
                # Fallback to matplotlib
                if viz_type == "bar_chart":
                    return self._create_bar_chart(df, query)
                elif viz_type == "line_chart":
                    return self._create_line_chart(df, query)
                elif viz_type == "pie_chart":
                    return self._create_pie_chart(df, query)
                elif viz_type == "scatter_plot":
                    return self._create_scatter_plot(df, query)
                elif viz_type == "histogram":
                    return self._create_histogram(df, query)
                else:
                    return self._create_default_chart(df, query)

        except Exception as e:
            logger.error(f"Visualization failed: {e}", exc_info=True)
            return None
    
    def _determine_visualization_type(self, df: pd.DataFrame, query: str) -> str:
        """
        Determine the best visualization type based on data and query
        """
        query_lower = query.lower()
        
        # Check for advanced visualization keywords
        if any(keyword in query_lower for keyword in ['heatmap', 'heat map', 'correlation matrix']):
            return "heatmap"
        elif any(keyword in query_lower for keyword in ['treemap', 'tree map', 'hierarchy']):
            return "treemap"
        elif any(keyword in query_lower for keyword in ['funnel', 'conversion']):
            return "funnel"
        elif any(keyword in query_lower for keyword in ['gauge', 'meter', 'kpi']):
            return "gauge"
        elif any(keyword in query_lower for keyword in ['box plot', 'boxplot', 'quartile']):
            return "box_plot"
        elif any(keyword in query_lower for keyword in ['violin plot', 'violinplot', 'density']):
            return "violin_plot"

        # Check for time-based queries
        time_keywords = ['trend', 'over time', 'daily', 'monthly', 'yearly', 'date']
        if any(keyword in query_lower for keyword in time_keywords):
            return "line_chart"

        # Check for comparison queries
        comparison_keywords = ['compare', 'vs', 'versus', 'top', 'best', 'worst']
        if any(keyword in query_lower for keyword in comparison_keywords):
            return "bar_chart"

        # Check for distribution queries
        distribution_keywords = ['distribution', 'percentage', 'proportion', 'share']
        if any(keyword in query_lower for keyword in distribution_keywords):
            return "pie_chart"

        # Check for correlation queries
        correlation_keywords = ['correlation', 'relationship', 'scatter']
        if any(keyword in query_lower for keyword in correlation_keywords):
            return "scatter_plot"
        
        # Default based on data structure
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        if len(numeric_cols) >= 2:
            return "scatter_plot"
        elif len(categorical_cols) > 0 and len(numeric_cols) > 0:
            return "bar_chart"
        elif len(numeric_cols) == 1:
            return "histogram"
        else:
            return "bar_chart"

    def _create_plotly_chart(self, df: pd.DataFrame, query: str, viz_type: str) -> str:
        """
        Create interactive Plotly charts

        Args:
            df: DataFrame containing the data
            query: Original query
            viz_type: Type of visualization to create

        Returns:
            Base64 encoded HTML string of the Plotly chart
        """
        try:
            if viz_type == "bar_chart":
                fig = self._create_plotly_bar_chart(df, query)
            elif viz_type == "line_chart":
                fig = self._create_plotly_line_chart(df, query)
            elif viz_type == "pie_chart":
                fig = self._create_plotly_pie_chart(df, query)
            elif viz_type == "scatter_plot":
                fig = self._create_plotly_scatter_plot(df, query)
            elif viz_type == "histogram":
                fig = self._create_plotly_histogram(df, query)
            elif viz_type == "heatmap":
                fig = self._create_plotly_heatmap(df, query)
            elif viz_type == "treemap":
                fig = self._create_plotly_treemap(df, query)
            elif viz_type == "funnel":
                fig = self._create_plotly_funnel(df, query)
            elif viz_type == "gauge":
                fig = self._create_plotly_gauge(df, query)
            elif viz_type == "box_plot":
                fig = self._create_plotly_box_plot(df, query)
            elif viz_type == "violin_plot":
                fig = self._create_plotly_violin_plot(df, query)
            else:
                fig = self._create_plotly_bar_chart(df, query)  # Default

            # Convert to HTML and then to base64
            html_str = pio.to_html(fig, include_plotlyjs='cdn', div_id="plotly-chart")
            html_bytes = html_str.encode('utf-8')
            html_b64 = base64.b64encode(html_bytes).decode('utf-8')

            return f"data:text/html;base64,{html_b64}"

        except Exception as e:
            logger.error(f"Plotly chart creation failed: {e}")
            # Fallback to matplotlib
            return self._create_matplotlib_fallback(df, query, viz_type)

    def _create_plotly_bar_chart(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive bar chart with Plotly"""
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]

            # Group by categorical column and sum numeric column
            grouped_data = df.groupby(x_col)[y_col].sum().reset_index()

            fig = px.bar(
                grouped_data,
                x=x_col,
                y=y_col,
                title=f"Analysis: {query[:50]}...",
                color=y_col,
                color_continuous_scale='viridis'
            )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16,
                xaxis_title=x_col.replace('_', ' ').title(),
                yaxis_title=y_col.replace('_', ' ').title(),
                showlegend=False
            )

            fig.update_traces(
                hovertemplate=f"<b>{x_col.title()}</b>: %{{x}}<br>" +
                             f"<b>{y_col.title()}</b>: %{{y:,.0f}}<extra></extra>"
            )

        else:
            # Create a simple bar chart with row indices
            fig = px.bar(
                x=list(range(len(df))),
                y=[1] * len(df),
                title="Data Overview"
            )

        return fig

    def _create_plotly_line_chart(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive line chart with Plotly"""
        # Find date/time columns
        date_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                date_cols.append(col)

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if date_cols and numeric_cols:
            x_col = date_cols[0]
            y_col = numeric_cols[0]

            # Convert to datetime if possible
            try:
                df[x_col] = pd.to_datetime(df[x_col])
                df = df.sort_values(x_col)
            except:
                pass

            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=f"Trend Analysis: {query[:50]}...",
                markers=True
            )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16,
                xaxis_title=x_col.replace('_', ' ').title(),
                yaxis_title=y_col.replace('_', ' ').title()
            )

        else:
            # Create a simple line chart
            fig = px.line(
                x=list(range(len(df))),
                y=df.iloc[:, 0] if len(df.columns) > 0 else [1] * len(df),
                title="Data Trend"
            )

        return fig

    def _create_plotly_pie_chart(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive pie chart with Plotly"""
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]

            # Group by categorical column and sum numeric column
            grouped_data = df.groupby(x_col)[y_col].sum().reset_index()

            fig = px.pie(
                grouped_data,
                values=y_col,
                names=x_col,
                title=f"Distribution: {query[:50]}..."
            )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16
            )

            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>" +
                             "Value: %{value:,.0f}<br>" +
                             "Percentage: %{percent}<extra></extra>"
            )

        else:
            # Create a simple pie chart
            fig = px.pie(
                values=[1] * min(len(df), 5),
                names=[f"Item {i+1}" for i in range(min(len(df), 5))],
                title="Data Distribution"
            )

        return fig

    def _create_plotly_scatter_plot(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive scatter plot with Plotly"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]

            # Add color dimension if there's a third numeric column
            color_col = numeric_cols[2] if len(numeric_cols) > 2 else None

            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"Correlation Analysis: {query[:50]}...",
                opacity=0.7
            )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16,
                xaxis_title=x_col.replace('_', ' ').title(),
                yaxis_title=y_col.replace('_', ' ').title()
            )

        else:
            # Create a simple scatter plot
            fig = px.scatter(
                x=list(range(len(df))),
                y=df.iloc[:, 0] if len(df.columns) > 0 else [1] * len(df),
                title="Data Scatter Plot"
            )

        return fig

    def _create_plotly_histogram(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive histogram with Plotly"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) > 0:
            col = numeric_cols[0]

            fig = px.histogram(
                df,
                x=col,
                title=f"Distribution: {query[:50]}...",
                nbins=20
            )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16,
                xaxis_title=col.replace('_', ' ').title(),
                yaxis_title='Frequency'
            )

        else:
            # Create a simple histogram
            fig = px.histogram(
                x=[1] * len(df),
                title="Data Distribution"
            )

        return fig

    def _create_plotly_heatmap(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive heatmap with Plotly"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) >= 2:
            # Create correlation heatmap
            corr_matrix = df[numeric_cols].corr()

            fig = px.imshow(
                corr_matrix,
                title=f"Correlation Heatmap: {query[:50]}...",
                color_continuous_scale='RdBu',
                aspect='auto'
            )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16
            )

        else:
            # Create a simple heatmap from the data
            fig = px.imshow(
                df.select_dtypes(include=[np.number]).values,
                title="Data Heatmap"
            )

        return fig

    def _create_plotly_treemap(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive treemap with Plotly"""
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            # Use first categorical column as labels and first numeric as values
            labels_col = categorical_cols[0]
            values_col = numeric_cols[0]

            # Group data if needed
            grouped_data = df.groupby(labels_col)[values_col].sum().reset_index()

            fig = px.treemap(
                grouped_data,
                path=[labels_col],
                values=values_col,
                title=f"Treemap: {query[:50]}..."
            )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16
            )

        else:
            # Create a simple treemap
            fig = px.treemap(
                names=[f"Item {i+1}" for i in range(min(len(df), 10))],
                values=[1] * min(len(df), 10),
                title="Data Treemap"
            )

        return fig

    def _create_plotly_funnel(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive funnel chart with Plotly"""
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            labels_col = categorical_cols[0]
            values_col = numeric_cols[0]

            # Sort by values for funnel effect
            sorted_data = df.sort_values(values_col, ascending=False)

            fig = go.Figure(go.Funnel(
                y=sorted_data[labels_col].head(10),
                x=sorted_data[values_col].head(10),
                textinfo="value+percent initial"
            ))

            fig.update_layout(
                title=f"Funnel Chart: {query[:50]}...",
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16
            )

        else:
            # Create a simple funnel
            fig = go.Figure(go.Funnel(
                y=[f"Stage {i+1}" for i in range(5)],
                x=[100, 80, 60, 40, 20],
                textinfo="value+percent initial"
            ))
            fig.update_layout(title="Sample Funnel Chart")

        return fig

    def _create_plotly_gauge(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive gauge chart with Plotly"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) >= 1:
            # Use first numeric column for gauge value
            value_col = numeric_cols[0]
            value = df[value_col].iloc[0] if len(df) > 0 else 0
            max_value = df[value_col].max() if len(df) > 0 else 100

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"KPI Gauge: {value_col.replace('_', ' ').title()}"},
                gauge={
                    'axis': {'range': [None, max_value]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, max_value * 0.5], 'color': "lightgray"},
                        {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': max_value * 0.9
                    }
                }
            ))

        else:
            # Create a sample gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=75,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Sample KPI"},
                gauge={'axis': {'range': [None, 100]}}
            ))

        fig.update_layout(
            template="plotly_white",
            font=dict(size=12),
            title_font_size=16
        )

        return fig

    def _create_plotly_box_plot(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive box plot with Plotly"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns

        if len(numeric_cols) >= 1:
            y_col = numeric_cols[0]

            if len(categorical_cols) >= 1:
                # Box plot by category
                x_col = categorical_cols[0]
                fig = px.box(
                    df,
                    x=x_col,
                    y=y_col,
                    title=f"Box Plot: {query[:50]}..."
                )
            else:
                # Single box plot
                fig = px.box(
                    df,
                    y=y_col,
                    title=f"Box Plot: {query[:50]}..."
                )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16
            )

        else:
            # Create a sample box plot
            fig = px.box(
                y=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                title="Sample Box Plot"
            )

        return fig

    def _create_plotly_violin_plot(self, df: pd.DataFrame, query: str) -> go.Figure:
        """Create an interactive violin plot with Plotly"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns

        if len(numeric_cols) >= 1:
            y_col = numeric_cols[0]

            if len(categorical_cols) >= 1:
                # Violin plot by category
                x_col = categorical_cols[0]
                fig = px.violin(
                    df,
                    x=x_col,
                    y=y_col,
                    title=f"Violin Plot: {query[:50]}...",
                    box=True
                )
            else:
                # Single violin plot
                fig = px.violin(
                    df,
                    y=y_col,
                    title=f"Violin Plot: {query[:50]}...",
                    box=True
                )

            fig.update_layout(
                template="plotly_white",
                font=dict(size=12),
                title_font_size=16
            )

        else:
            # Create a sample violin plot
            fig = px.violin(
                y=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                title="Sample Violin Plot",
                box=True
            )

        return fig

    def _create_matplotlib_fallback(self, df: pd.DataFrame, query: str, viz_type: str) -> str:
        """Fallback to matplotlib if Plotly fails"""
        logger.warning("Falling back to matplotlib for visualization")

        if viz_type == "bar_chart":
            return self._create_bar_chart(df, query)
        elif viz_type == "line_chart":
            return self._create_line_chart(df, query)
        elif viz_type == "pie_chart":
            return self._create_pie_chart(df, query)
        elif viz_type == "scatter_plot":
            return self._create_scatter_plot(df, query)
        elif viz_type == "histogram":
            return self._create_histogram(df, query)
        else:
            return self._create_default_chart(df, query)

    def _create_bar_chart(self, df: pd.DataFrame, query: str) -> str:
        """Create a bar chart"""
        plt.figure(figsize=(10, 6))
        
        # Find categorical and numeric columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            # Use first categorical column as x-axis and first numeric as y-axis
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            
            # Group by categorical column and sum numeric column
            grouped_data = df.groupby(x_col)[y_col].sum().reset_index()
            
            plt.bar(grouped_data[x_col], grouped_data[y_col])
            plt.xlabel(x_col.replace('_', ' ').title())
            plt.ylabel(y_col.replace('_', ' ').title())
            plt.title(f"Analysis: {query[:50]}...")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
        
        return self._save_plot_to_base64()
    
    def _create_line_chart(self, df: pd.DataFrame, query: str) -> str:
        """Create a line chart"""
        plt.figure(figsize=(10, 6))
        
        # Find date/time columns
        date_cols = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated']):
                date_cols.append(col)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if date_cols and numeric_cols:
            x_col = date_cols[0]
            y_col = numeric_cols[0]
            
            # Convert to datetime if possible
            try:
                df[x_col] = pd.to_datetime(df[x_col])
                df = df.sort_values(x_col)
            except:
                pass
            
            plt.plot(df[x_col], df[y_col], marker='o')
            plt.xlabel(x_col.replace('_', ' ').title())
            plt.ylabel(y_col.replace('_', ' ').title())
            plt.title(f"Trend Analysis: {query[:50]}...")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
        
        return self._save_plot_to_base64()
    
    def _create_pie_chart(self, df: pd.DataFrame, query: str) -> str:
        """Create a pie chart"""
        plt.figure(figsize=(10, 8))
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            
            # Group by categorical column and sum numeric column
            grouped_data = df.groupby(x_col)[y_col].sum()
            
            plt.pie(grouped_data.values, labels=grouped_data.index, autopct='%1.1f%%')
            plt.title(f"Distribution: {query[:50]}...")
            plt.axis('equal')
        
        return self._save_plot_to_base64()
    
    def _create_scatter_plot(self, df: pd.DataFrame, query: str) -> str:
        """Create a scatter plot"""
        plt.figure(figsize=(10, 6))
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            
            plt.scatter(df[x_col], df[y_col], alpha=0.6)
            plt.xlabel(x_col.replace('_', ' ').title())
            plt.ylabel(y_col.replace('_', ' ').title())
            plt.title(f"Correlation Analysis: {query[:50]}...")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
        
        return self._save_plot_to_base64()
    
    def _create_histogram(self, df: pd.DataFrame, query: str) -> str:
        """Create a histogram"""
        plt.figure(figsize=(10, 6))
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            
            plt.hist(df[col], bins=20, alpha=0.7, edgecolor='black')
            plt.xlabel(col.replace('_', ' ').title())
            plt.ylabel('Frequency')
            plt.title(f"Distribution: {query[:50]}...")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
        
        return self._save_plot_to_base64()
    
    def _create_default_chart(self, df: pd.DataFrame, query: str) -> str:
        """Create a default chart when other types don't fit"""
        plt.figure(figsize=(10, 6))
        
        # Simple bar chart of first few rows
        if len(df) > 0:
            # Use first column as labels, second as values if available
            if len(df.columns) >= 2:
                x_data = df.iloc[:10, 0].astype(str)
                y_data = df.iloc[:10, 1] if df.iloc[:10, 1].dtype in ['int64', 'float64'] else range(len(x_data))
            else:
                x_data = range(len(df))
                y_data = range(len(df))
            
            plt.bar(x_data, y_data)
            plt.xlabel('Index')
            plt.ylabel('Value')
            plt.title(f"Data Overview: {query[:50]}...")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
        
        return self._save_plot_to_base64()
    
    def _save_plot_to_base64(self) -> str:
        """Save the current plot to a base64 encoded string"""
        try:
            # Save plot to bytes buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Close the plot to free memory
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            print(f"Failed to save plot: {e}")
            plt.close()
            return None
    
    def create_summary_chart(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Create a summary chart showing key metrics
        """
        if not data:
            return None
        
        try:
            df = pd.DataFrame(data)
            
            plt.figure(figsize=(12, 8))
            
            # Create subplots for different metrics
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle('Data Summary Dashboard', fontsize=16)
            
            # Plot 1: Record count by category (if categorical data exists)
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                col = categorical_cols[0]
                value_counts = df[col].value_counts().head(5)
                axes[0, 0].bar(value_counts.index, value_counts.values)
                axes[0, 0].set_title(f'Top 5 {col.title()}')
                axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Plot 2: Numeric data distribution
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                axes[0, 1].hist(df[col], bins=20, alpha=0.7)
                axes[0, 1].set_title(f'{col.title()} Distribution')
            
            # Plot 3: Data overview
            axes[1, 0].text(0.1, 0.5, f'Total Records: {len(df)}\nColumns: {len(df.columns)}', 
                           transform=axes[1, 0].transAxes, fontsize=12)
            axes[1, 0].set_title('Data Overview')
            axes[1, 0].axis('off')
            
            # Plot 4: Missing data
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                axes[1, 1].bar(missing_data.index, missing_data.values)
                axes[1, 1].set_title('Missing Data')
                axes[1, 1].tick_params(axis='x', rotation=45)
            else:
                axes[1, 1].text(0.5, 0.5, 'No Missing Data', 
                               transform=axes[1, 1].transAxes, ha='center', va='center')
                axes[1, 1].set_title('Missing Data')
            
            plt.tight_layout()
            return self._save_plot_to_base64()
            
        except Exception as e:
            print(f"Summary chart creation failed: {e}")
            return None 