from nafld_kbd_table import nafld_kbd_table
from nafld_kbd_search import nafld_kbd_search
from nafld_kbd_stats import nafld_kbd_stats
from nafld_kbd_nav import nafld_kbd_nav
from PIL import Image
import json
import streamlit as st
import pandas as pd

import warnings
def warn(*args, **kwargs): pass
warnings.warn = warn

from ketcher import ketcher

icon = Image.open('./icon.png')
st.set_page_config(page_title='NAFLD KBS', layout='wide', page_icon=icon)

@st.cache
def read_data():
    trials = pd.read_excel('./data/Clinical_Trials.xlsx').set_index('Trial_ID')
    drugs = pd.read_excel('./data/Drugs.xlsx').set_index('Drug_ID')
    targets = pd.read_excel('./data/Therapy_Targets.xlsx').set_index('Target_ID')
    return trials, drugs, targets

trials, drugs, targets = read_data()

class NAFLD_KBD:
    def __init__(self) -> None:
        self.header = st.empty()
        self.body = st.empty()
        self.footer = st.empty()
        session_init = [
            ('nav_click_time', 0),
            ('current_page', 'home'),
            ('item_id', None),
            ('query_type', None),
            ('query', None),
        ]
        for key, value in session_init:
            st.session_state[key] = value

    def update_session_from_link(self):
        for key, value in st.experimental_get_query_params().items():
            st.session_state[key] = value[0]

    def set_link(self, params):
        tmp = {}
        for i in params.keys():
            if params[i] is not None:
                tmp[i] = params[i]
        st.experimental_set_query_params(**tmp)

    def dataframe_transform(self, df, data_type):
        df_data = {'type': data_type, 'data': []}
        for i in df.index:
            tmp = json.loads(df.loc[i].to_json())
            tmp[data_type.capitalize()[:-1]+'_ID'] = i
            df_data['data'].append(tmp)
        return df_data
    
    def mock(self, data_type):
        df_data = {'type': data_type, 'data': []}
        samples = globals()[data_type].sample(n=3)
        for i in samples.index:
            tmp = json.loads(samples.loc[i].to_json())
            tmp[data_type.capitalize()[:-1]+'_ID'] = i
            df_data['data'].append(tmp)
        return df_data
    
    def simple_format_details(self, details):
        for i in details.keys():
            st.markdown(f"**{i}**")
            st.markdown(details[i])

    def exec_table_command(self, command):
        if command['action'] == 'details':
            self.set_link({
                'nav_click_time': st.session_state['nav_click_time'],
                'current_page': f'{command["data_type"]}_details',
                'item_id': command['item_id']
            })
            st.experimental_rerun()
        elif command['action'] == 'relations':
            st.markdown("<label>📚  RELATED ENTRIES</label>", unsafe_allow_html=True)
            for i in ['trial', 'drug', 'target']:
                if i != command["data_type"]:
                    nafld_kbd_table(self.mock(i+'s'), command_buttons_disabled=True)

    def navigation(self, nav_click_time):
        with self.header:
            # Navbar
            nav_component_value = nafld_kbd_nav(nav_click_time=nav_click_time)
            if not nav_component_value == 0:
                if int(nav_component_value['nav_click_time']) != int(st.session_state.nav_click_time):
                    self.set_link(nav_component_value)
                    st.experimental_rerun()

    def search(self):
        query_type = st.session_state.query_type
        query = st.session_state.query
        if query_type == 'trial':  # trial search
            res = trials[
                trials["Source_ID"].str.contains(query, case=False, na=False) +
                trials["Title"].str.contains(query, case=False, na=False)
            ]
            res_data = self.dataframe_transform(res, 'trials')
        elif query_type == 'drug':  # drug search
            res = drugs[
                drugs["Drug_Name"].str.contains(query, case=False, na=False) +
                drugs["DrugBank_ID"].str.contains(query, case=False, na=False)
            ]
            res_data = self.dataframe_transform(res, 'drugs')
        elif query_type == 'target':  # target search
            res = targets[
                targets["Target_Name"].str.contains(query, case=False, na=False) +
                targets["Target_GENE"].str.contains(query, case=False, na=False)
            ]
            res_data = self.dataframe_transform(res, 'targets')
        elif query_type == 'smiles':  # TO DO: structure search
            res = drugs[drugs["SMILES"].str.contains(query, case=False, na=False)]
            res_data = self.dataframe_transform(res, 'targets')

        return res_data

    def page_home(self):
        with st.container():
            # Basic Search
            basic_search = nafld_kbd_search(name="basic_search", key="basic_search")
            if basic_search:
                self.set_link({
                    'nav_click_time': st.session_state.nav_click_time,
                    'current_page': "search_results",
                    'query_type': basic_search['query_type'],
                    'query': basic_search['query']
                })
                st.experimental_rerun()
            # Statistics
            st.markdown("<label>📊  STATISTICS</label>", unsafe_allow_html=True)
            clickedCard = nafld_kbd_stats(stats=[x.shape[0] for x in [trials, drugs, targets]])
            if clickedCard:
                self.set_link({
                    'nav_click_time': st.session_state['nav_click_time'],
                    'current_page': clickedCard
                })
                st.experimental_rerun()
            # Structure Search
            st.markdown("<label>🔍  STRUCTURE SEARCH</label>", unsafe_allow_html=True)
            smiles = ketcher(name="structure_search", key="structure_search")
            if smiles:
                self.set_link({
                    'nav_click_time': st.session_state.nav_click_time,
                    'current_page': "search_results",
                    'query_type': 'smiles',
                    'query': smiles
                })
                st.experimental_rerun()

    def page_search_results(self):
        with st.container():
            st.markdown(
                f"<label>🔎  {st.session_state.query_type.upper()} SEARCH RESULTS FOR: '{st.session_state.query}' </label>",
                unsafe_allow_html=True
            )
            res_data = self.search()
            command = nafld_kbd_table(res_data)
            if command:
                self.exec_table_command(command)

    def page_trials(self):
        with st.container():
            st.markdown("<label>💉  CLINICAL TRIALS</label>", unsafe_allow_html=True)
            trials_data = self.dataframe_transform(trials, 'trials')
            command = nafld_kbd_table(trials_data)
            if command:
                self.exec_table_command(command)

    def page_trial_details(self):
        trial_id = st.session_state.item_id
        with st.container():
            self.simple_format_details(trials.loc[int(trial_id)].to_dict())

    def page_drugs(self):
        with st.container():
            st.markdown("<label>💊  DRUGS</label>", unsafe_allow_html=True)
            drugs_data = self.dataframe_transform(drugs, 'drugs')
            command = nafld_kbd_table(drugs_data)
            if command:
                self.exec_table_command(command)

    def page_drug_details(self):
        drug_id = st.session_state.item_id
        with st.container():
            self.simple_format_details(drugs.loc[int(drug_id)].to_dict())

    def page_targets(self):
        with st.container():
            st.markdown("<label>🧬  TARGETS</label>", unsafe_allow_html=True)
            targets_data = self.dataframe_transform(targets, 'targets')
            command = nafld_kbd_table(targets_data)
            if command:
                self.exec_table_command(command)

    def page_target_details(self):
        target_id = st.session_state.item_id
        with st.container():
            self.simple_format_details(targets.loc[int(target_id)].to_dict())

    def page_about(self):
        st.info('This is About Page')

    def run(self):
        self.update_session_from_link()
        self.navigation(st.session_state.nav_click_time)
        with self.body:
            # call method from string name
            getattr(self, 'page_' + st.session_state.current_page, None)()
        # set proper URL for each page
        self.set_link({x: st.session_state[x] for x in [
            'nav_click_time',
            'current_page',
            'query_type',
            'query',
            'item_id'
        ]})


app = NAFLD_KBD()
app.run()

# CSS
st.markdown("""
<style>
    header,footer { visibility: hidden; height: 0; }
    label { font-size: 24px !important; font-weight: bold !important; }
    .block-container { max-width: 84%; padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)
