
# Advanced Production-Grade Periodic Table Explorer
# A Streamlit application that displays an interactive periodic table
# with sophisticated UI elements and professional-grade design

import streamlit as st
import pandas as pd
import requests
import json
import numpy as np
import plotly.graph_objects as go
import os # For path joining if using local HTML file for component

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

# Custom CSS for production-grade UI (same as before)
st.markdown("""
<style>
    /* Main app styling */
    .main {
        background-color: #f5f7f9;
        color: #1e1e1e;
    }
    .main h1 {
        color: #1e3a8a; /* Darker blue */
        font-weight: 600;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb; /* Light gray border */
    }
    .element-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 5px solid var(--category-color, #3b82f6); /* Dynamic color based on category */
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f3f4f6; /* Light gray for inactive tabs */
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6; /* Blue for active tab */
        color: white;
    }
    /* Table styling (from previous examples) */
    .dataframe { /* Target Streamlit's default table rendering for consistency */
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        border-radius: 10px; /* Rounded corners for table */
        overflow: hidden; /* Ensures border radius is respected */
    }
    .dataframe thead tr {
        background-color: #3b82f6; /* Header background */
        color: #ffffff; /* Header text color */
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
        background-color: #f3f3f3; /* Zebra striping for rows */
    }
    .dataframe tbody tr:last-of-type {
        border-bottom: 2px solid #3b82f6; /* Emphasize table end */
    }
    /* Custom sidebar styling */
    .css-1d391kg { /* This class might change with Streamlit updates, target more generically if needed */
        background-color: #f1f5f9; /* Lighter sidebar background */
    }
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main h1 { font-size: 2rem; }
        .element-card { padding: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# App state management
class AppState:
    def __init__(self):
        self.category_colors = {
            "diatomic nonmetal": "#7dd3fc", # Light blue for diatomic nonmetals
            "noble gas": "#a78bfa", # Purple for noble gases
            "alkali metal": "#fb923c", # Orange for alkali metals
            "alkaline earth metal": "#facc15", # Yellow for alkaline earth metals
            "metalloid": "#4ade80", # Green for metalloids
            "polyatomic nonmetal": "#22d3ee", # Cyan for polyatomic nonmetals
            "post-transition metal": "#a3a3a3", # Gray for post-transition metals
            "transition metal": "#f472b6", # Pink for transition metals
            "lanthanide": "#d8b4fe", # Lighter purple for lanthanides
            "actinide": "#fda4af", # Lighter red/pink for actinides
            "unknown, probably transition metal": "#e5e5e5",
            "unknown, probably metalloid": "#e5e5e5",
            "unknown, probably post-transition metal": "#e5e5e5",
            "unknown, predicted to be noble gas": "#e5e5e5",
            "unknown, but predicted to be an alkali metal": "#e5e5e5",
            "nonmetal": "#67e8f9", # Default nonmetal color if more specific not available
            "unknown": "#e0e0e0" # Default for unknown
        }

    def get_element_color(self, category):
        # Normalize category string for matching
        normalized_category = category.lower().replace('-', ' ') if isinstance(category, str) else "unknown"
        
        # Direct match
        if normalized_category in self.category_colors:
            return self.category_colors[normalized_category]
        
        # Partial match for keys like "unknown, probably transition metal"
        for key, color in self.category_colors.items():
            if normalized_category.startswith(key.split(',')[0]): # e.g. "unknown"
                return color # this logic might need refinement based on desired fallback
        
        # General fallback
        if "nonmetal" in normalized_category: return self.category_colors["nonmetal"]
        if "metal" in normalized_category: return self.category_colors["transition metal"] # A general metal color
        
        return self.category_colors["unknown"]


state = AppState()

@st.cache_data(ttl=3600)
def load_element_data():
    try:
        url = "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json"
        response = requests.get(url)
        response.raise_for_status() # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        data = response.json()
        elements_df = pd.json_normalize(data['elements'])
        
        # Ensure essential columns exist, providing defaults if necessary
        required_cols = {
            'name': 'Unknown', 'symbol': '?', 'number': 0, 'category': 'unknown',
            'period': 0, 'group': 0, 'xpos': 0, 'ypos': 0, 'atomic_mass': 0.0,
            'electron_configuration': '', 'phase': 'Unknown'
        }
        for col, default_val in required_cols.items():
            if col not in elements_df.columns:
                elements_df[col] = default_val
        
        # Convert types to ensure consistency
        elements_df['number'] = pd.to_numeric(elements_df['number'], errors='coerce').fillna(0).astype(int)
        elements_df['period'] = pd.to_numeric(elements_df['period'], errors='coerce').fillna(0).astype(int)
        elements_df['group'] = pd.to_numeric(elements_df['group'], errors='coerce').fillna(0).astype(int)
        elements_df['xpos'] = pd.to_numeric(elements_df['xpos'], errors='coerce').fillna(0).astype(int)
        elements_df['ypos'] = pd.to_numeric(elements_df['ypos'], errors='coerce').fillna(0).astype(int)

        # Handle NaN values in strings after normalization
        for col in ['name', 'symbol', 'category', 'electron_configuration', 'phase']:
             elements_df[col] = elements_df[col].fillna(required_cols.get(col, 'Unknown'))

        return elements_df
    except requests.exceptions.RequestException as e:
        st.error(f"Network error loading element data: {e}")
    except json.JSONDecodeError as e:
        st.error(f"Error decoding element data JSON: {e}")
    except KeyError as e:
        st.error(f"Unexpected JSON structure for element data (missing 'elements' key?): {e}")
    # Fallback to a minimal dataset if loading fails
    st.warning("Using a minimal fallback dataset for elements.")
    return pd.DataFrame([
        {"name": "Hydrogen", "symbol": "H", "number": 1, "category": "diatomic nonmetal", "period": 1, "group": 1, "xpos": 1, "ypos": 1, "atomic_mass": 1.008, "electron_configuration": "1s1", "phase": "Gas"},
        {"name": "Helium", "symbol": "He", "number": 2, "category": "noble gas", "period": 1, "group": 18, "xpos": 18, "ypos": 1, "atomic_mass": 4.0026, "electron_configuration": "1s2", "phase": "Gas"},
        {"name": "Lithium", "symbol": "Li", "number": 3, "category": "alkali metal", "period": 2, "group": 1, "xpos": 1, "ypos": 2, "atomic_mass": 6.94, "electron_configuration": "[He] 2s1", "phase": "Solid"},
        {"name": "Carbon", "symbol": "C", "number": 6, "category": "polyatomic nonmetal", "period": 2, "group": 14, "xpos": 14, "ypos": 2, "atomic_mass": 12.011, "electron_configuration": "[He] 2s2 2p2", "phase": "Solid"},
        {"name": "Oxygen", "symbol": "O", "number": 8, "category": "diatomic nonmetal", "period": 2, "group": 16, "xpos": 16, "ypos": 2, "atomic_mass": 15.999, "electron_configuration": "[He] 2s2 2p4", "phase": "Gas"},
    ])


def format_electron_configuration(config_str):
    if not isinstance(config_str, str): return ""
    # Simple formatter, can be expanded
    return config_str.replace(" ", "&nbsp;").replace("s", "s<sup>").replace("p", "p<sup>").replace("d", "d<sup>").replace("f", "f<sup>") + ("</sup>" * config_str.count("["))


def create_element_card(element, color):
    # (Same as your well-styled card function)
    st.markdown(f"""
    <div class="element-card" style="--category-color: {color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0; font-size: 2.5rem;">{element.get('symbol', 'N/A')}</h2>
            <div style="text-align: right;">
                <span style="font-size: 2rem; font-weight: 600;">{element.get('number', 'N/A')}</span>
                <div style="font-size: 0.9rem; color: #6b7280;">{element.get('atomic_mass', 0.0):.4f} u</div>
            </div>
        </div>
        <h3 style="margin-top: 0.5rem; margin-bottom: 1rem; font-size: 1.8rem;">{element.get('name', 'N/A')}</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.875rem; color: #6b7280;">Category</div>
                <div style="font-weight: 500;">{str(element.get('category', 'N/A')).title()}</div>
            </div>
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.875rem; color: #6b7280;">Period • Group</div>
                <div style="font-weight: 500;">{element.get('period', 'N/A')} • {element.get('group', 'N/A')}</div>
            </div>
            <div style="flex: 1; min-width: 120px;">
                <div style="font-size: 0.875rem; color: #6b7280;">Phase at STP</div>
                <div style="font-weight: 500;">{str(element.get('phase', 'Unknown')).title()}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Plotly functions (Electron Shell, Molecular Structure - kept from previous)
def create_electron_shell_visualization(electron_config_str):
    # (Your existing robust function)
    fig = go.Figure()
    # Placeholder logic, replace with your actual shell visualization
    shells_data = {}
    if isinstance(electron_config_str, str):
        # Example parsing: "1s2 2s2 2p6"
        # This is highly simplified; a real parser is complex.
        parts = electron_config_str.replace('[', '').replace(']', ' ').split()
        current_shell = 0
        for part in parts:
            if part.endswith('s') or part.endswith('p') or part.endswith('d') or part.endswith('f'):
                 # Handles core like "He" or "Ne" by skipping them for this simple viz
                continue
            try:
                shell_num = int(part[0])
                electrons = int(part[2:])
                shells_data[shell_num] = shells_data.get(shell_num, 0) + electrons
            except (ValueError, IndexError):
                pass # Ignore malformed parts for this simple viz
    
    if not shells_data: # Fallback if parsing fails or empty
        fig.add_annotation(text="Electron shell data not available or unparsable.", showarrow=False)
        return fig

    max_shell = max(shells_data.keys()) if shells_data else 0
    
    # Nucleus
    fig.add_shape(type="circle", xref="x", yref="y", x0=-0.5, y0=-0.5, x1=0.5, y1=0.5, fillcolor="tomato")
    
    for shell_num in range(1, max_shell + 1):
        radius = shell_num * 1.5
        fig.add_shape(type="circle", xref="x", yref="y",
                      x0=-radius, y0=-radius, x1=radius, y1=radius,
                      line_color="lightblue", line_width=1, fillcolor="rgba(0,0,0,0)")
        
        electrons = shells_data.get(shell_num, 0)
        if electrons > 0:
            for i in range(electrons):
                angle = (i / electrons) * 2 * np.pi
                ex = radius * np.cos(angle)
                ey = radius * np.sin(angle)
                fig.add_trace(go.Scatter(x=[ex], y=[ey], mode='markers', marker=dict(color='blue', size=8)))

    fig.update_layout(
        title_text="Electron Shells (Simplified)",
        xaxis=dict(visible=False, range=[-max_shell*2, max_shell*2]),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, range=[-max_shell*2, max_shell*2]),
        showlegend=False,
        width=300, height=300,
        margin=dict(t=50, b=0, l=0, r=0)
    )
    return fig


def generate_molecular_visualization(formula_str):
    # (Your existing placeholder/example function)
    fig = go.Figure()
    # Simplified: just places spheres for first few letters of formula
    num_atoms = min(len(formula_str), 5)
    x_coords = np.random.rand(num_atoms) * 5
    y_coords = np.random.rand(num_atoms) * 5
    z_coords = np.random.rand(num_atoms) * 5
    colors = ['red', 'blue', 'green', 'yellow', 'purple']
    
    fig.add_trace(go.Scatter3d(
        x=x_coords, y=y_coords, z=z_coords,
        mode='markers',
        marker=dict(size=12, color=[colors[i%len(colors)] for i in range(num_atoms)], opacity=0.8)
    ))
    fig.update_layout(
        title_text=f"Simplified Structure of {formula_str}",
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'),
        width=400, height=400,
        margin=dict(t=50, b=0, l=0, r=0)
    )
    return fig

# --- Interactive Plotly Periodic Table via Custom Component ---
def create_plotly_periodic_table_figure(elements_df, filtered_elements_df, selected_element_number=None):
    fig = go.Figure()
    
    # Determine max x and y for layout
    max_x = elements_df['xpos'].max() if not elements_df.empty else 18
    max_y = elements_df['ypos'].max() if not elements_df.empty else 10

    for index, element in elements_df.iterrows():
        is_filtered_out = element['number'] not in filtered_elements_df['number'].values
        
        opacity = 0.3 if is_filtered_out else 1.0
        marker_line_color = 'black'
        marker_line_width = 0
        if selected_element_number and element['number'] == selected_element_number:
            marker_line_color = '#FFD700' # Gold outline for selected
            marker_line_width = 4
            opacity = 1.0 # Ensure selected is fully visible

        element_color = state.get_element_color(element.get('category', 'unknown'))

        fig.add_trace(go.Scatter(
            x=[element['xpos']],
            y=[max_y - element['ypos'] +1], # Invert y-axis for typical table layout
            mode='markers+text',
            marker=dict(
                size=35, # Adjust size as needed
                color=element_color,
                opacity=opacity,
                line=dict(color=marker_line_color, width=marker_line_width),
                symbol='square'
            ),
            text=f"<b>{element['symbol']}</b>",
            textfont=dict(size=10, color='black' if opacity > 0.5 else '#777'), # Darker text for visible items
            textposition="middle center",
            hoverinfo='text',
            hovertext=(
                f"<b>{element['name']} ({element['symbol']})</b><br>"
                f"Number: {element['number']}<br>"
                f"Mass: {element.get('atomic_mass', 0.0):.3f}<br>"
                f"Category: {str(element.get('category', 'N/A')).title()}"
            ),
            customdata=[element['number']] # Store element number for click events
        ))

    fig.update_layout(
        xaxis=dict(range=[0, max_x + 1], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        yaxis=dict(range=[0, max_y + 1], showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        plot_bgcolor='#f5f7f9', # Match app background
        paper_bgcolor='#f5f7f9',
        height= (max_y + 1) * 45, # Dynamic height based on number of periods
        clickmode='event' # Important for capturing click events
    )
    return fig


# HTML for the custom Plotly component
PLOTLY_COMPONENT_HTML = """
<div id="plotlyChartContainer" style="width:100%; height:100%;"></div>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<script>
const chartDiv = document.getElementById('plotlyChartContainer');
const figData = {fig_data_placeholder}; // Will be replaced by Python
const figLayout = {fig_layout_placeholder}; // Will be replaced by Python

Plotly.newPlot(chartDiv, figData, figLayout, {{responsive: true}}).then(gd => {{
    gd.on('plotly_click', eventData => {{
        if (eventData.points.length > 0) {{
            const clickedPoint = eventData.points[0];
            if (clickedPoint.customdata !== undefined) {{
                Streamlit.setComponentValue({{
                    type: "element_click",
                    number: clickedPoint.customdata[0] // customdata is an array
                }});
            }}
        }}
    }});
}});

// Adjust height of iframe to content
function sendHeight() {{
    Streamlit.setFrameHeight(document.getElementById('plotlyChartContainer').offsetHeight + 20);
}}
// Ensure Plotly has rendered before sending height
const observer = new MutationObserver(function(mutationsList, observer) {{
    for(let mutation of mutationsList) {{
        if (mutation.type === 'childList' || mutation.type === 'attributes') {{
            sendHeight();
            // observer.disconnect(); // Disconnect after first render if static, or keep for dynamic
            break;
        }}
    }}
}});
observer.observe(chartDiv, {{ attributes: true, childList: true, subtree: true }});
window.addEventListener('resize', sendHeight);
// Initial height setting after a short delay for rendering
setTimeout(sendHeight, 200); 
</script>
"""

def display_element_details(element_series, elements_df_full):
    if element_series is None or element_series.empty:
        st.info("Select an element from the periodic table to view its details, or use the search/filter options.")
        return

    # Ensure element_series is a Series (it should be if iloc[0] was used)
    if not isinstance(element_series, pd.Series):
        st.error("Invalid element data provided for details display.")
        return

    category = element_series.get('category', 'unknown')
    color = state.get_element_color(category)
    create_element_card(element_series, color)

    tabs_titles = ["Overview", "Physical Properties", "Chemical Properties", "Visualizations", "Applications & Isotopes"]
    tabs = st.tabs(tabs_titles)

    with tabs[0]: # Overview
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown("### Summary")
            st.markdown(element_series.get('summary', "No summary available."))
            st.markdown("### Basic Information")
            basic_info = {
                "Discovered by": element_series.get('discovered_by', 'N/A'),
                "Named by": element_series.get('named_by', 'N/A'),
                "Electron Config.": element_series.get('electron_configuration_semantic', element_series.get('electron_configuration', 'N/A')),
            }
            for key, value in basic_info.items(): st.markdown(f"**{key}:** {value}")
        with col2:
            img_name = str(element_series.get('name', '')).lower()
            if img_name:
                st.image(f"https://images-of-elements.com/s/{img_name}.jpg", caption=element_series.get('name'), use_container_width=True, width=150)
            else:
                st.image("https://via.placeholder.com/150?text=No+Image", caption="Image N/A", use_container_width=True)
            st.markdown(f"**Category:** {str(element_series.get('category', 'N/A')).title()}")

    with tabs[1]: # Physical Properties
        st.markdown("### Physical Properties")
        physical_props = {
            "Melting Point": f"{element_series.get('melt', 'N/A')} K",
            "Boiling Point": f"{element_series.get('boil', 'N/A')} K",
            "Density": f"{element_series.get('density', 'N/A')} g/cm³",
            "Phase at STP": str(element_series.get('phase', 'Unknown')).title(),
            "Electronegativity (Pauling)": element_series.get('electronegativity_pauling', 'N/A'),
            "Atomic Radius": f"{element_series.get('atomic_radius', 'N/A')} pm",
        }
        st.table(pd.DataFrame(physical_props.items(), columns=["Property", "Value"]))

    with tabs[2]: # Chemical Properties
        st.markdown("### Chemical Properties")
        chem_props = {
            "Atomic Number": element_series.get('number', 'N/A'),
            "Atomic Mass": f"{element_series.get('atomic_mass', 0.0):.4f} u",
            "Oxidation States": element_series.get('common_oxidation_states', element_series.get('oxidation_states', 'N/A')), # Prefer common if available
            "Electron Affinity": f"{element_series.get('electron_affinity', 'N/A')} kJ/mol",
            "Ionization Energies (eV)": str(element_series.get('ionization_energies', ['N/A'])[:3]) + "...", # Show first few
        }
        st.table(pd.DataFrame(chem_props.items(), columns=["Property", "Value"]))

    with tabs[3]: # Visualizations
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            st.markdown("#### Electron Shells")
            fig_e = create_electron_shell_visualization(element_series.get('electron_configuration', ''))
            st.plotly_chart(fig_e, use_container_width=True)
        with viz_col2:
            st.markdown("#### Molecular (Example)")
            fig_m = generate_molecular_visualization(element_series.get('symbol', 'X'))
            st.plotly_chart(fig_m, use_container_width=True)

    with tabs[4]: # Applications & Isotopes
        st.markdown("### Applications")
        st.markdown(element_series.get('uses', "Specific applications not detailed."))
        st.markdown("### Isotopes")
        # The JSON structure for isotopes might be nested or complex.
        # This is a placeholder; actual parsing would depend on 'PeriodicTableJSON.json' structure for isotopes.
        st.markdown("Isotope data might require specific parsing from the source JSON.")


# Main app logic
def main():
    st.title("Interactive Periodic Table Explorer")
    st.markdown("Explore chemical elements with detailed interactive visualizations. Click an element on the table!")

    if 'selected_element_number' not in st.session_state:
        st.session_state.selected_element_number = 1 # Default to Hydrogen

    elements_df = load_element_data()
    if elements_df.empty:
        st.error("Element data could not be loaded. Application cannot proceed.")
        return

    # --- Sidebar for Filtering ---
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/components/python/streamlit/images/logo.svg", width=150) # Streamlit logo
        st.markdown("## Filter Elements")

        all_categories = sorted(elements_df['category'].dropna().unique())
        selected_categories = st.multiselect("Category", all_categories, default=all_categories)

        all_phases = sorted(elements_df['phase'].dropna().unique())
        selected_phases = st.multiselect("Phase at STP", all_phases, default=all_phases)
        
        search_query = st.text_input("Search by Name or Symbol").lower()

        filtered_elements_df = elements_df.copy()
        if selected_categories:
            filtered_elements_df = filtered_elements_df[filtered_elements_df['category'].isin(selected_categories)]
        if selected_phases:
            filtered_elements_df = filtered_elements_df[filtered_elements_df['phase'].isin(selected_phases)]
        if search_query:
            filtered_elements_df = filtered_elements_df[
                filtered_elements_df['name'].str.lower().str.contains(search_query) |
                filtered_elements_df['symbol'].str.lower().str.contains(search_query)
            ]
        
        st.markdown("### Legend")
        # Create a more compact legend
        legend_html = "<div style='display: flex; flex-wrap: wrap; gap: 5px;'>"
        unique_cats_in_view = filtered_elements_df['category'].unique() if not filtered_elements_df.empty else all_categories
        for cat in unique_cats_in_view[:10]: # Show up to 10 for brevity
            color = state.get_element_color(cat)
            legend_html += f"<div style='display: flex; align-items: center;'><div style='width: 10px; height: 10px; background-color: {color}; margin-right: 3px; border-radius: 2px;'></div><small>{str(cat).title()}</small></div>"
        if len(unique_cats_in_view) > 10: legend_html += "<small>...</small>"
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

        # Allow direct selection as a fallback or alternative
        element_names_map = pd.Series(elements_df.number.values, index=elements_df.name).to_dict()
        # Ensure selected_element_number corresponds to a valid name for the selectbox
        current_selection_name = None
        if st.session_state.selected_element_number:
            match = elements_df[elements_df['number'] == st.session_state.selected_element_number]
            if not match.empty:
                current_selection_name = match.iloc[0]['name']
        
        selected_name_from_box = st.selectbox(
            "Or Select Element:", 
            options=elements_df['name'].sort_values().tolist(), 
            index=elements_df['name'].sort_values().tolist().index(current_selection_name) if current_selection_name and current_selection_name in elements_df['name'].sort_values().tolist() else 0
        )
        if selected_name_from_box and (not current_selection_name or selected_name_from_box != current_selection_name) :
            st.session_state.selected_element_number = element_names_map[selected_name_from_box]
            # No st.rerun() here to avoid loop if selectbox itself causes a rerun

    # --- Main Content Area (Periodic Table and Details) ---
    col_table, col_details = st.columns([2,1]) # Adjust ratio as needed, table larger

    with col_table:
        st.subheader("Periodic Table Grid")
        plotly_fig = create_plotly_periodic_table_figure(elements_df, filtered_elements_df, st.session_state.selected_element_number)
        
        # Prepare data for the HTML component
        fig_data_json = json.dumps(plotly_fig.data, cls=plotly.utils.PlotlyJSONEncoder)
        fig_layout_json = json.dumps(plotly_fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

        component_html_rendered = PLOTLY_COMPONENT_HTML.replace("{fig_data_placeholder}", fig_data_json)
        component_html_rendered = component_html_rendered.replace("{fig_layout_placeholder}", fig_layout_json)
        
        # Calculate dynamic height for component based on figure's layout height
        dynamic_component_height = plotly_fig.layout.height if plotly_fig.layout and plotly_fig.layout.height else 600
        
        clicked_element_data = st.components.v1.html(component_html_rendered, height=dynamic_component_height + 40, scrolling=False)

        if clicked_element_data and clicked_element_data.get("type") == "element_click":
            clicked_number = clicked_element_data.get("number")
            if clicked_number != st.session_state.selected_element_number:
                 st.session_state.selected_element_number = clicked_number
                 st.rerun() # Rerun to update selection and details pane

    with col_details:
        st.subheader("Element Details")
        selected_element_series = None
        if st.session_state.selected_element_number:
            match = elements_df[elements_df['number'] == st.session_state.selected_element_number]
            if not match.empty:
                selected_element_series = match.iloc[0]
        
        display_element_details(selected_element_series, elements_df)

    # Footer
    st.markdown("---")
    st.markdown("Developed with Streamlit | Data: [PeriodicTableJSON](https://github.com/Bowserinator/Periodic-Table-JSON) | Images: [images-of-elements.com](https://images-of-elements.com)")

if __name__ == "__main__":
    # Need to import plotly for the JSON encoder if not already globally imported
    import plotly 
    main()

