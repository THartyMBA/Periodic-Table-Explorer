
# Advanced Production-Grade Periodic Table Explorer
# A Streamlit application that displays an interactive periodic table
# with sophisticated UI elements and professional-grade design

import streamlit as st
import pandas as pd
import requests
import json
import time
from io import BytesIO
import base64
from PIL import Image
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu
import altair as alt
import os

# Set page configuration with custom theme
st.set_page_config(
    page_title="Interactive Periodic Table Explorer",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.chemicool.com/',
        'Report a bug': "mailto:support@periodictable.app",
        'About': "# Advanced Periodic Table Explorer\nExplore chemical elements with detailed interactive visualizations."
    }
)

# Custom CSS for production-grade UI
st.markdown("""
<style>
    /* Main app styling */
    .main {
        background-color: #f5f7f9;
        color: #1e1e1e;
    }
    
    /* Header styling */
    .main h1 {
        color: #1e3a8a;
        font-weight: 600;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    /* Card styling for element details */
    .element-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 5px solid var(--category-color, #3b82f6);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f3f4f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }
    
    /* Table styling */
    .dataframe {
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        font-family: sans-serif;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 10px;
        overflow: hidden;
    }
    
    .dataframe thead tr {
        background-color: #3b82f6;
        color: white;
        text-align: left;
    }
    
    .dataframe th,
    .dataframe td {
        padding: 12px 15px;
    }
    
    .dataframe tbody tr {
        border-bottom: 1px solid #dddddd;
    }
    
    .dataframe tbody tr:nth-of-type(even) {
        background-color: #f3f3f3;
    }
    
    .dataframe tbody tr:last-of-type {
        border-bottom: 2px solid #3b82f6;
    }
    
    /* Element grid styling */
    .element {
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    .element:hover {
        transform: scale(1.08);
        box-shadow: 0 6px 10px rgba(0,0,0,0.2) !important;
        z-index: 100;
        cursor: pointer;
    }
    
    /* Loading animation */
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
    }
    
    /* Custom button styling */
    .custom-button {
        background-color: #3b82f6;
        color: white;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        text-align: center;
        transition: background-color 0.2s;
        border: none;
        cursor: pointer;
    }
    .custom-button:hover {
        background-color: #2563eb;
    }
    
    /* Tooltip styling */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #1e1e1e;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Custom sidebar styling */
    .css-1d391kg {
        background-color: #f1f5f9;
    }
    
    /* Media query for responsive design */
    @media only screen and (max-width: 768px) {
        .element-card {
            padding: 1rem;
        }
        
        .main h1 {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# App state management
class AppState:
    def __init__(self):
        self.selected_element = None
        self.elements_data = None
        self.category_colors = {
            "alkali metal": "#ff8a65",
            "alkaline earth metal": "#ffb74d",
            "transition metal": "#ffd54f",
            "post-transition metal": "#dce775",
            "metalloid": "#aed581",
            "nonmetal": "#4fc3f7",
            "halogen": "#80deea",
            "noble gas": "#9575cd",
            "lanthanoid": "#f48fb1",
            "actinoid": "#f06292",
            "unknown": "#e0e0e0"
        }
        
    def get_element_color(self, category):
        """Return the color for a given element category"""
        return self.category_colors.get(category.lower(), self.category_colors["unknown"])

# Initialize app state
state = AppState()

@st.cache_data(ttl=3600)
def load_element_data():
    """
    Load periodic table data from a reliable source
    Returns a DataFrame with element information
    """
    try:
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("Loading element data...")
        
        # Try to load data from an online source
        url = "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json"
        response = requests.get(url)
        
        if response.status_code != 200:
            raise Exception(f"Failed to load data: HTTP {response.status_code}")
            
        # Update progress
        progress_bar.progress(50)
        status_text.text("Processing element data...")
        
        data = json.loads(response.text)
        elements = pd.DataFrame(data['elements'])
        
        # Add additional feature: electron configuration visualization
        elements['electron_display'] = elements['electron_configuration'].apply(
            lambda x: format_electron_configuration(x) if isinstance(x, str) else ""
        )
        
        # Update progress
        progress_bar.progress(100)
        status_text.empty()
        progress_bar.empty()
        
        return elements
    except Exception as e:
        st.warning(f"Error loading complete element data: {str(e)}. Using simplified dataset.")
        progress_bar.empty()
        status_text.empty()
        
        # Create a basic dataset with essential information for a fallback
        elements = []
        
        # Period 1
        elements.append({"name": "Hydrogen", "symbol": "H", "number": 1, "category": "nonmetal", "period": 1, "group": 1, 
                        "phase": "gas", "atomic_mass": 1.008, "electron_configuration": "1s1"})
        elements.append({"name": "Helium", "symbol": "He", "number": 2, "category": "noble gas", "period": 1, "group": 18,
                        "phase": "gas", "atomic_mass": 4.0026, "electron_configuration": "1s2"})
        
        # Add a few more elements for basic functionality
        elements.append({"name": "Lithium", "symbol": "Li", "number": 3, "category": "alkali metal", "period": 2, "group": 1,
                        "phase": "solid", "atomic_mass": 6.94, "electron_configuration": "1s2 2s1"})
        elements.append({"name": "Carbon", "symbol": "C", "number": 6, "category": "nonmetal", "period": 2, "group": 14,
                        "phase": "solid", "atomic_mass": 12.011, "electron_configuration": "1s2 2s2 2p2"})
        elements.append({"name": "Oxygen", "symbol": "O", "number": 8, "category": "nonmetal", "period": 2, "group": 16,
                        "phase": "gas", "atomic_mass": 15.999, "electron_configuration": "1s2 2s2 2p4"})
        
        return pd.DataFrame(elements)

def format_electron_configuration(config):
    """Format electron configuration for display"""
    parts = config.split()
    formatted = []
    for part in parts:
        if part[0].isdigit():
            orbital = part[:2]
            electrons = part[2:]
            formatted.append(f"{orbital}<sup>{electrons}</sup>")
        else:
            formatted.append(part)
    return " ".join(formatted)

def create_element_card(element, color):
    """Create a custom styled card for element details"""
    st.markdown(f"""
    <div class="element-card" style="--category-color: {color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0; font-size: 2.5rem;">{element['symbol']}</h2>
            <div style="text-align: right;">
                <span style="font-size: 2rem; font-weight: 600;">{element['number']}</span>
                <div style="font-size: 0.9rem; color: #6b7280;">{element['atomic_mass']:.4f} u</div>
            </div>
        </div>
        <h3 style="margin-top: 0.5rem; margin-bottom: 1rem; font-size: 1.8rem;">{element['name']}</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.875rem; color: #6b7280;">Category</div>
                <div style="font-weight: 500;">{element['category'].title()}</div>
            </div>
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.875rem; color: #6b7280;">Period • Group</div>
                <div style="font-weight: 500;">{element.get('period', 'N/A')} • {element.get('group', 'N/A')}</div>
            </div>
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.875rem; color: #6b7280;">Phase at STP</div>
                <div style="font-weight: 500;">{element.get('phase', 'Unknown').title()}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def generate_molecular_visualization(formula):
    """Generate a placeholder molecular visualization"""
    # In a real app, this would call a chemistry visualization library
    # For this example, we'll create a simple placeholder
    fig = go.Figure()
    
    # Generate random 3D coordinates for atoms (placeholder)
    np.random.seed(sum(ord(c) for c in formula))
    n_atoms = len(formula.replace('+', '').replace('-', ''))
    n_atoms = max(min(n_atoms * 2, 10), 3)  # Scale based on formula length
    
    x = np.random.rand(n_atoms) * 10 - 5
    y = np.random.rand(n_atoms) * 10 - 5
    z = np.random.rand(n_atoms) * 10 - 5
    
    # Create atoms (spheres)
    elements = ['C', 'H', 'O', 'N', 'P', 'S', 'F', 'Cl', 'Br', 'I']
    colors = ['black', 'white', 'red', 'blue', 'orange', 'yellow', 'green', 'green', 'brown', 'purple']
    
    for i in range(n_atoms):
        element_idx = i % len(elements)
        fig.add_trace(go.Scatter3d(
            x=[x[i]], y=[y[i]], z=[z[i]],
            mode='markers',
            marker=dict(
                size=10,
                color=colors[element_idx],
                opacity=0.8,
                line=dict(width=0.5, color='#333')
            ),
            text=elements[element_idx],
            hoverinfo='text'
        ))
    
    # Create bonds (lines)
    for i in range(n_atoms-1):
        fig.add_trace(go.Scatter3d(
            x=[x[i], x[i+1]], y=[y[i], y[i+1]], z=[z[i], z[i+1]],
            mode='lines',
            line=dict(width=4, color='#999'),
            hoverinfo='none'
        ))
    
    # Set figure layout
    fig.update_layout(
        title=f"Structure of {formula}",
        margin=dict(l=0, r=0, b=0, t=30),
        showlegend=False,
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode='cube'
        )
    )
    
    return fig

def create_electron_shell_visualization(electron_config):
    """Create a visualization of electron shells"""
    try:
        # Parse electron configuration to extract shells
        shells = {'K': 0, 'L': 0, 'M': 0, 'N': 0, 'O': 0, 'P': 0, 'Q': 0}
        
        if isinstance(electron_config, str):
            parts = electron_config.split()
            for part in parts:
                if part[0].isdigit() and len(part) >= 3:
                    shell = int(part[0]) - 1
                    electrons = int(part[2:]) if part[2:].isdigit() else 1
                    
                    # Map numerical shell to letter notation
                    shell_letters = ['K', 'L', 'M', 'N', 'O', 'P', 'Q']
                    if shell < len(shell_letters):
                        shells[shell_letters[shell]] += electrons
        
        # Create visualization
        fig = go.Figure()
        
        # Nuclear radius and shell scaling
        nucleus_radius = 10
        shell_scaling = 15
        max_electrons = 32  # For scaling size
        
        # Draw nucleus
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(
                size=nucleus_radius * 2,
                color='#ff6b6b',
                line=dict(width=1, color='#c44569')
            ),
            name='Nucleus'
        ))
        
        # Draw electron shells
        shell_idx = 0
        for shell, electrons in shells.items():
            if electrons == 0:
                continue
                
            shell_idx += 1
            radius = nucleus_radius + (shell_idx * shell_scaling)
            
            # Draw the shell circle
            theta = np.linspace(0, 2*np.pi, 100)
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            
            fig.add_trace(go.Scatter(
                x=x, y=y,
                mode='lines',
                line=dict(color='#b2bec3', width=1, dash='dash'),
                name=f'Shell {shell}'
            ))
            
            # Add electrons
            if electrons > 0:
                electron_theta = np.linspace(0, 2*np.pi, electrons, endpoint=False)
                electron_x = radius * np.cos(electron_theta)
                electron_y = radius * np.sin(electron_theta)
                
                # Scale electron size based on number of electrons
                electron_size = max(4, 8 - (electrons / max_electrons) * 6)
                
                fig.add_trace(go.Scatter(
                    x=electron_x, y=electron_y,
                    mode='markers',
                    marker=dict(
                        size=electron_size,
                        color='#3498db',
                        line=dict(width=1, color='#2980b9')
                    ),
                    name=f'{shell} electrons: {electrons}'
                ))
        
        # Set layout
        fig.update_layout(
            title=f"Electron Shell Diagram",
            xaxis=dict(
                scaleanchor="y",
                scaleratio=1,
                showticklabels=False,
                zeroline=False,
                showgrid=False
            ),
            yaxis=dict(
                showticklabels=False,
                zeroline=False,
                showgrid=False
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=400,
            width=500
        )
        
        return fig
    
    except Exception as e:
        # Return a placeholder on error
        fig = go.Figure()
        fig.add_annotation(
            text=f"Could not generate electron shell visualization<br>{str(e)}",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(
            xaxis=dict(showticklabels=False, zeroline=False, showgrid=False),
            yaxis=dict(showticklabels=False, zeroline=False, showgrid=False),
            height=400
        )
        return fig

def create_periodic_table_grid(elements_df, filtered_elements):
    """Create an interactive periodic table grid"""
    # Add custom HTML/CSS for the grid layout
    html_content = """
    <div class="grid-container" style="display: grid; grid-template-columns: repeat(18, 70px); gap: 2px; justify-content: center; margin-top: 20px;">
    """
    
    # Dictionary to map element number to its position in the grid
    element_positions = {}
    for _, elem in elements_df.iterrows():
        if 'group' in elem and 'period' in elem:
            try:
                period = int(elem['period'])
                group = int(elem['group'])
                element_positions[elem['number']] = (period, group)
            except (ValueError, TypeError):
                pass
    
    # Generate cells for the periodic table
    for row in range(1, 10):  # Periods 1-9
        for col in range(1, 19):  # Groups 1-18
            # Find the element at this position
            element = None
            for _, elem in elements_df.iterrows():
                if elem.get('period') == row and elem.get('group') == col:
                    element = elem
                    break
            
            # Special handling for lanthanides and actinides
            if row == 6 and col == 3:
                element = {"number": "57-71", "symbol": "La-Lu", "name": "Lanthanides", "category": "lanthanoid"}
            if row == 7 and col == 3:
                element = {"number": "89-103", "symbol": "Ac-Lr", "name": "Actinides", "category": "actinoid"}
            
            # Add the element cell or an empty cell
            if element is not None:
                # Get category and color
                category = element.get('category', 'unknown')
                color = state.get_element_color(category)
                
                # Determine if element is filtered
                elem_id = element.get('number', '')
                filtered = False
                if filtered_elements is not None and len(filtered_elements) > 0:
                    # Check if this element is not in the filtered list
                    filtered = isinstance(elem_id, (int, str)) and str(elem_id).isdigit() and int(elem_id) not in filtered_elements['number'].values
                
                opacity = "0.35" if filtered else "1.0"
                
                # Create the element cell with hover effects and click event
                html_content += f"""
                <div 
                    class="element" 
                    id="element-{elem_id}"
                    onclick="handleElementClick({elem_id})"
                    style="
                        background-color: {color}; 
                        opacity: {opacity};
                        width: 70px;
                        height: 70px;
                        border-radius: 4px;
                        padding: 4px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                        transition: all 0.2s;
                        position: relative;
                    "
                >
                    <div style="font-size: 10px; text-align: left; color: rgba(0,0,0,0.7);">{elem_id}</div>
                    <div style="font-size: 18px; font-weight: bold; text-align: center; margin-top: 4px;">{element.get('symbol', '')}</div>
                    <div style="font-size: 9px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">{element.get('name', '')}</div>
                    <div style="font-size: 8px; text-align: center; margin-top: 1px; color: rgba(0,0,0,0.6);">{element.get('atomic_mass', '')}</div>
                </div>
                """
            else:
                # Empty cell
                html_content += '<div style="width: 70px; height: 70px;"></div>'
        
        # Add line break after each period
        html_content += '<div style="flex-basis: 100%; height: 0;"></div>'
    
    # Add lanthanides row (elements 57-71)
    html_content += '<div style="grid-column: 1 / span 18; height: 20px;"></div>'
    for num in range(57, 72):
        element = None
        for _, elem in elements_df.iterrows():
            if elem.get('number') == num:
                element = elem
                break
        
        if element is not None:
            category = element.get('category', 'unknown')
            color = state.get_element_color(category)
            
            # Determine if element is filtered
            elem_id = element.get('number', '')
            filtered = False
            if filtered_elements is not None and len(filtered_elements) > 0:
                filtered = elem_id not in filtered_elements['number'].values
            
            opacity = "0.35" if filtered else "1.0"
            
            html_content += f"""
            <div 
                class="element" 
                id="element-{elem_id}"
                onclick="handleElementClick({elem_id})"
                style="
                    background-color: {color}; 
                    opacity: {opacity};
                    width: 70px;
                    height: 70px;
                    border-radius: 4px;
                    padding: 4px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                    transition: all 0.2s;
                "
            >
                <div style="font-size: 10px; text-align: left; color: rgba(0,0,0,0.7);">{elem_id}</div>
                <div style="font-size: 18px; font-weight: bold; text-align: center; margin-top: 4px;">{element.get('symbol', '')}</div>
                <div style="font-size: 9px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">{element.get('name', '')}</div>
                <div style="font-size: 8px; text-align: center; margin-top: 1px; color: rgba(0,0,0,0.6);">{element.get('atomic_mass', '')}</div>
            </div>
            """
    
    # Add actinides row (elements 89-103)
    html_content += '<div style="flex-basis: 100%; height: 0;"></div>'
    for num in range(89, 104):
        element = None
        for _, elem in elements_df.iterrows():
            if elem.get('number') == num:
                element = elem
                break
        
        if element is not None:
            category = element.get('category', 'unknown')
            color = state.get_element_color(category)
            
            # Determine if element is filtered
            elem_id = element.get('number', '')
            filtered = False
            if filtered_elements is not None and len(filtered_elements) > 0:
                filtered = elem_id not in filtered_elements['number'].values
            
            opacity = "0.35" if filtered else "1.0"
            
            html_content += f"""
            <div 
                class="element" 
                id="element-{elem_id}"
                onclick="handleElementClick({elem_id})"
                style="
                    background-color: {color}; 
                    opacity: {opacity};
                    width: 70px;
                    height: 70px;
                    border-radius: 4px;
                    padding: 4px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                    transition: all 0.2s;
                "
            >
                <div style="font-size: 10px; text-align: left; color: rgba(0,0,0,0.7);">{elem_id}</div>
                <div style="font-size: 18px; font-weight: bold; text-align: center; margin-top: 4px;">{element.get('symbol', '')}</div>
                <div style="font-size: 9px; text-align: center; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">{element.get('name', '')}</div>
                <div style="font-size: 8px; text-align: center; margin-top: 1px; color: rgba(0,0,0,0.6);">{element.get('atomic_mass', '')}</div>
            </div>
            """
    
    html_content += "</div>"
    
    # Add JavaScript for handling element clicks
    html_content += """
    <script>
    function handleElementClick(elementNumber) {
        // Send the element number to Streamlit via session state
        const data = {
            number: elementNumber,
            instanceId: window.frameElement.id
        };
        
        window.parent.postMessage({
            type: "streamlit:setComponentValue",
            value: data
        }, "*");
    }
    </script>
    """
    
    return html_content

def display_element_details(element, elements_df):
    """Display detailed information about the selected element"""
    if element is None:
        st.info("Select an element from the periodic table to view its details.")
        return
    
    category = element.get('category', 'unknown')
    color = state.get_element_color(category)
    
    # Create a custom styled card for the element
    create_element_card(element, color)
    
    # Create detailed tabs for the element
    tabs = st.tabs(["Overview", "Physical Properties", "Chemical Properties", "Visualizations", "Applications"])
    
    with tabs[0]:  # Overview tab
        col1, col2 = st.columns([3, 2])
        
        with col1:
            if 'summary' in element:
                st.markdown("### Summary")
                st.markdown(element['summary'])
            
            st.markdown("### Basic Information")
            basic_info = {
                "Discovery": element.get('discovered_by', 'Unknown'),
                "Named By": element.get('named_by', 'Unknown'),
                "Year of Discovery": element.get('year', 'Unknown'),
                "Electron Configuration": element.get('electron_configuration', 'Unknown'),
                "Oxidation States": element.get('oxidation_states', 'Unknown')
            }
            
            for key, value in basic_info.items():
                if value != 'Unknown':
                    st.markdown(f"**{key}:** {value}")
        
        with col2:
            # Display element image if available
            if 'number' in element and isinstance(element['number'], int):
                # Try to load image from URL or show placeholder
                try:
                    image_url = f"https://images-of-elements.com/s/{element['name'].lower()}.jpg"
                    st.image(image_url, caption=f"{element['name']} sample", use_column_width=True)
                except:
                    st.image("https://via.placeholder.com/300x200?text=Image+Not+Available", 
                             caption="Element image not available", use_column_width=True)
            
            # Show position in periodic table
            st.markdown("### Position in Periodic Table")
            st.markdown(f"**Group:** {element.get('group', 'N/A')}")
            st.markdown(f"**Period:** {element.get('period', 'N/A')}")
            st.markdown(f"**Block:** {element.get('block', 'N/A')}")
            st.markdown(f"**Category:** {element.get('category', 'N/A').title()}")
    
    with tabs[1]:  # Physical Properties tab
        st.markdown("### Physical Properties")
        physical_props = {
            "Melting Point": f"{element.get('melt', 'N/A')} K",
            "Boiling Point": f"{element.get('boil', 'N/A')} K",
            "Density": f"{element.get('density', 'N/A')} g/cm³",
            "Phase at STP": element.get('phase', 'Unknown').title(),
            "Electronegativity": element.get('electronegativity_pauling', 'N/A'),
            "Ionization Energy": f"{element.get('ionization_energies', ['N/A'])[0]} eV" if 'ionization_energies' in element and element['ionization_energies'] else 'N/A',
            "Atomic Radius": f"{element.get('atomic_radius', 'N/A')} pm",
            "Covalent Radius": f"{element.get('covalent_radius', 'N/A')} pm"
        }
        
        props_df = pd.DataFrame(physical_props.items(), columns=["Property", "Value"])
        st.table(props_df)
    
    with tabs[2]:  # Chemical Properties tab
        st.markdown("### Chemical Properties")
        chem_props = {
            "Atomic Number": element.get('number', 'N/A'),
            "Atomic Mass": f"{element.get('atomic_mass', 'N/A')} u",
            "Electron Configuration": element.get('electron_configuration', 'N/A'),
            "Oxidation States": element.get('oxidation_states', 'N/A'),
            "Crystal Structure": element.get('crystal_structure', 'N/A'),
            "Molar Heat Capacity": f"{element.get('molar_heat', 'N/A')} J/(mol·K)"
        }
        
        chem_df = pd.DataFrame(chem_props.items(), columns=["Property", "Value"])
        st.table(chem_df)
    
    with tabs[3]:  # Visualizations tab
        viz_tab1, viz_tab2 = st.columns(2)
        
        with viz_tab1:
            st.markdown("#### Electron Shell Diagram")
            electron_fig = create_electron_shell_visualization(element.get('electron_configuration', ''))
            st.plotly_chart(electron_fig, use_container_width=True)
        
        with viz_tab2:
            st.markdown("#### Molecular Structure (Simplified)")
            # Placeholder for molecular visualization
            formula = element.get('symbol', 'X') + (element.get('name', '')[0:2] if len(element.get('name', '')) > 2 else 'X2')
            mol_fig = generate_molecular_visualization(formula)
            st.plotly_chart(mol_fig, use_container_width=True)
    
    with tabs[4]:  # Applications tab
        st.markdown("### Common Applications")
        # Placeholder for applications information
        st.markdown("This section would typically include information about industrial and practical applications of the element.")
        st.markdown("- Application 1")
        st.markdown("- Application 2")
        st.markdown("- Application 3")
        
        st.markdown("### Isotopes")
        if 'isotopes' in element and element['isotopes']:
            isotopes_data = [{"Mass Number": iso.get('mass_number', 'N/A'), "Abundance": iso.get('abundance', 'N/A'), "Half-life": iso.get('half_life', 'N/A')} for iso in element['isotopes']]
            isotopes_df = pd.DataFrame(isotopes_data)
            st.table(isotopes_df)
        else:
            st.markdown("No isotope information available for this element.")

# Main app logic
def main():
    # Initialize session state if not already done
    if 'selected_element_number' not in st.session_state:
        st.session_state.selected_element_number = None
    
    # Load element data
    with st.spinner("Loading periodic table data..."):
        elements_df = load_element_data()
    
    # Header
    st.markdown("# Interactive Periodic Table Explorer")
    st.markdown("Explore the properties and characteristics of chemical elements with interactive visualizations.")
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x80?text=Periodic+Table+App", use_column_width=True)
        st.markdown("### Filter Elements")
        
        # Category filter
        categories = sorted(elements_df['category'].unique())
        selected_categories = st.multiselect("Filter by Category", categories, default=categories)
        
        # Phase filter
        phases = sorted(elements_df['phase'].dropna().unique())
        selected_phases = st.multiselect("Filter by Phase at STP", phases, default=phases)
        
        # Period filter
        periods = sorted(elements_df['period'].dropna().unique())
        selected_periods = st.multiselect("Filter by Period", periods, default=periods)
        
        # Group filter
        groups = sorted(elements_df['group'].dropna().unique())
        selected_groups = st.multiselect("Filter by Group", groups, default=groups)
        
        # Apply filters
        filtered_df = elements_df[
            (elements_df['category'].isin(selected_categories)) &
            (elements_df['phase'].isin(selected_phases)) &
            (elements_df['period'].isin(selected_periods)) &
            (elements_df['group'].isin(selected_groups))
        ]
        
        st.markdown("### Quick Search")
        search_term = st.text_input("Search by Name or Symbol", "")
        if search_term:
            search_term = search_term.lower()
            filtered_df = filtered_df[
                (filtered_df['name'].str.lower().str.contains(search_term)) |
                (filtered_df['symbol'].str.lower().str.contains(search_term))
            ]
        
        st.markdown("### Legend")
        for cat, color in state.category_colors.items():
            st.markdown(f"<div style='display: flex; align-items: center; margin-bottom: 5px;'><div style='width: 12px; height: 12px; background-color: {color}; margin-right: 5px;'></div>{cat.title()}</div>", unsafe_allow_html=True)
    
    # Main content area
    tab1, tab2 = st.tabs(["Periodic Table", "Element Details"])
    
    with tab1:
        st.markdown("### Interactive Periodic Table")
        st.markdown("Click on any element to view detailed information.")
        
        # Create and display the periodic table grid
        grid_html = create_periodic_table_grid(elements_df, filtered_df)
        st.markdown(grid_html, unsafe_allow_html=True)
        
        # Check for element selection (this would work in a real Streamlit app)
        if st.session_state.selected_element_number:
            selected_num = st.session_state.selected_element_number
            selected_element = elements_df[elements_df['number'] == selected_num].iloc[0] if selected_num in elements_df['number'].values else None
            if selected_element is not None:
                state.selected_element = selected_element
                st.markdown(f"Selected element: **{selected_element['name']}**. Switch to the Element Details tab to view more information.")
    
    with tab2:
        display_element_details(state.selected_element, elements_df)
    
    # Footer
    st.markdown("---")
    st.markdown("Developed with Streamlit | Data sourced from public chemistry databases")

if __name__ == "__main__":
    main()


