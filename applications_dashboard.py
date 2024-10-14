import pandas as pd
import io

import dash
from dash import Dash, dash_table, html, dcc, Input, Output

def clean_upcoming_batch_df(upcoming_batch_df):
    upcoming_batch_df = upcoming_batch_df.replace("", None)
    upcoming_batch_df = upcoming_batch_df[pd.notna(upcoming_batch_df['Applied Date'])].copy()
    upcoming_batch_df = upcoming_batch_df[upcoming_batch_df['Registration Batch'] == current_batch_column]
    upcoming_batch_df = upcoming_batch_df.drop_duplicates(subset=['SP ID'], keep='first')
    upcoming_batch_df = upcoming_batch_df.dropna(subset=['SP ID']).replace('', pd.NA).dropna(subset=['SP ID'])
    upcoming_batch_df = upcoming_batch_df.sort_values(by='SP ID', key=lambda col: col.astype(int))
    # Assign each applicant into a wait time bucket
    # bin_edges = [-1, 1, 2, 3, 4, float('inf')]
    # bin_labels = ['1', '2', '3', '4', '5+']
    # upcoming_batch_df["Call Count Bucketed"] = pd.cut(upcoming_batch_df['Call Count'].apply(lambda x: int(x)), bins=bin_edges, labels=bin_labels)
    # upcoming_batch_df["Call Count Bucketed"] = upcoming_batch_df["Call Count Bucketed"].cat.add_categories('unknown')
    # upcoming_batch_df["Call Count Bucketed"] = upcoming_batch_df["Call Count Bucketed"].fillna("unknown")
    return upcoming_batch_df


def clean_all_batches_df(all_batches_df):
    all_batches_df = all_batches_df.replace("", None)
    all_batches_df = all_batches_df[pd.notna(all_batches_df['Applied Date'])].copy()
    all_batches_df = all_batches_df.drop_duplicates(subset=['SP ID'], keep='first')
    all_batches_df = all_batches_df.dropna(subset=['SP ID']).replace('', pd.NA).dropna(subset=['SP ID'])
    all_batches_df = all_batches_df.sort_values(by='SP ID', key=lambda col: col.astype(int))
    return all_batches_df


def dated_columns_stats(all_batches_df):

    column_stats_cols_csv_str = "Applied Date,All Set Date,Full Profile Submission Date,Interview Done On,Final Approval Decision Datetime" # @param {"type":"string","placeholder":"2023 - 2024, 2024 - 2025"}
    column_stats_cols = column_stats_cols_csv_str.split(',')

    def create_columns_index(app_df, target_columns):
        stats_dict = dict()
        for col in target_columns:
            stats_dict[col] = {
                'Total Count': app_df[col].dropna().count(),
            }
        return stats_dict

    def create_columns_stats_df(all_batches_df, target_columns):
        stats_dict = create_columns_index(all_batches_df, target_columns)
        registration_batches = all_batches_df['Registration Batch'].unique().tolist()

        for col in target_columns:
            for batch in registration_batches:
                stats_dict[col][batch + ' Count'] = all_batches_df[all_batches_df['Registration Batch'] == batch][col].count()
                stats_dict[col][batch + ' Meditator Count'] = all_batches_df[(all_batches_df['Registration Batch'] == batch) & (all_batches_df['IE Status'] == 'Completed the program')][col].count()
                stats_dict[col][batch + ' Non-Meditator Count'] = all_batches_df[(all_batches_df['Registration Batch'] == batch) & (all_batches_df['IE Status'] != 'Completed the program')][col].count()

        stats_df = pd.DataFrame(stats_dict).T
        stats_df = stats_df.reset_index().rename(columns={'index': 'Column Name'})
        stats_df = stats_df.reset_index().rename(columns={'index': 'Index'})
        return stats_df
    stats_df = create_columns_stats_df(all_batches_df, column_stats_cols)
    return stats_df


def date_non_date_columns(batch_df):
    target_column_names = [
        'Pre-Reg Call Status',
        'Pre-Registration Status',
        'Pending Other Reason',
        'Status of IE Interest',
        'Is Starmarked?',
        'Starmark Review',
        'SDP Tagged - Status',
        'Sdp Tagged Review Comments',
        'Is IE Pending and All set?',
        'All Set Date',
        'Full profile form sent date',
        'Profile Form Status',
        'Full Profile Submission Date',
        'Webinar Attended?',
        'Webinar Reflection form filled?',
        'Webinar Reflection form filled on',
        'Interview Done On',
        'Interview State',
        'Previous Interview State',
        'Interview Done By',
        'Interviewer Opinion',
        'Concerns',
        'Interview Opinion On',
        'Health Assessment Email Sent Date',
        'Health Assessment Form Status',
        'Health Assessment Submission Date',
        'Health Assessment',
        'Doctor Approval Decision',
        'Doctor Approval decision date',
        'Ready For Review Date',
        'Reviewer Decision',
        'VRO/OCO Feedback Status',
        'Review Decision On',
        'Final Approval Decision Datetime',
        'Final Approver Decision',
        'Final Approval Form Status',
        'Final Approval Email Send Datetime',
        'Arrival Batch',
        'Arrival Status',
        'Onboarding Status',
        'Onboarding Call Status',
        'Are you coming as couple?',
        'Are you Coming with Laptop?',
        'Mode of Travel',
        'Verification Status',
        'VMS Checkin Status',
        'SP Epass Status',
        'Arrival Datetime',
        'Cancellation Date',
        'Cancellation Reason',
        'Previous Status'
        ]

    # Function to check if a column is a date column
    def is_date_column(series):
        try:
            series_nona = series.dropna()
            if len(series_nona) == 0:
                return False
            # Try converting the entire series to datetime
            pd.to_datetime(series_nona, format='%Y-%m-%d %H:%M:%S')
            return True
        except (ValueError, TypeError):
            return False

    # Note that there will be some missing columns from both column sets if the series is empty.
    date_columns = [col for col in target_column_names if is_date_column(batch_df[col]) and len(batch_df[col].dropna()) != 0]
    date_columns = ['Applied Date'] + date_columns
    non_date_columns = [col for col in target_column_names if col not in date_columns and len(batch_df[col].dropna()) != 0]
    return date_columns, non_date_columns


def create_dated_columns_counts_df(batch_df, date_columns):
    date_columns_df = batch_df[date_columns].copy()
    date_columns_df.index = batch_df["SP ID"].copy()
    # Convert all date string columns to pandas datetime types.
    for col in date_columns:
        date_columns_df[col] = pd.to_datetime(date_columns_df[col], errors='coerce', format='%Y-%m-%d %H:%M:%S')

    # Get the last stage reached by each user
    date_columns_df['Last Stage'] = date_columns_df.apply(lambda row: row.last_valid_index(), axis=1)
    # Get the timestamp of the last stage
    date_columns_df['Last Timestamp'] = date_columns_df.apply(lambda row: row.dropna().iloc[-2], axis=1)
    now = pd.Timestamp.now()
    date_columns_df['Time Since Last Stage'] = (now - date_columns_df['Last Timestamp']).dt.days
    bin_edges = [01, 10, 20, 30, 40, 50, float('inf')]
    bin_labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51+']
    # Assign each applicant into a wait time bucket
    date_columns_df['Wait Time Bucket'] = pd.cut(date_columns_df['Time Since Last Stage'], bins=bin_edges, labels=bin_labels)

    # Create wait time distribution (histogram) across applicants per stage
    date_col_counts_df = date_columns_df.groupby(['Last Stage', 'Wait Time Bucket']).size().unstack(fill_value=0)
    last_stages_ordered = [col for col in date_columns if col in set(date_col_counts_df.index.tolist())]
    date_col_counts_df = date_col_counts_df.reindex(last_stages_ordered)

    # Add Aggregate States columns for each stage.
    last_dated_stage_counts_df = date_columns_df['Last Stage'].value_counts()
    avg_waiting_times_df = date_columns_df.groupby('Last Stage')['Time Since Last Stage'].mean().round(1)
    date_col_counts_df['Total Waiting Applicants'] = last_dated_stage_counts_df.copy()
    date_col_counts_df["Average Waiting Time"] = avg_waiting_times_df.copy()
    return date_col_counts_df, date_columns_df

def stage_status_mappings(date_columns):
    sp_status_mapping_df = pd.read_csv(io.StringIO('''
        SP Status,Column
        Pre-registration,Pre-Reg Call Status
        Pre-registration,Pre-Registration Status
        Pre-registration,Pending Other Reason
        Pre-registration,Status of IE Interest
        Pre-registration,Is Starmarked?
        Pre-registration,Starmark Review
        Pre-registration,SDP Tagged - Status
        Pre-registration,Sdp Tagged Review Comments
        Pre-registration,Is IE Pending and All set?
        Pre-registration,All Set Date
        Registration,Full profile form sent date
        Registration,Profile Form Status
        Registration,Full Profile Submission Date
        Registration,Webinar Attended?
        Registration,Webinar Reflection form filled?
        Registration,Webinar Reflection form filled on
        Interview,Interview Done On
        Interview,Interview State
        Interview,Previous Interview State
        Interview,Interview Done By
        Interview,Interviewer Opinion
        Interview,Concerns
        Interview,Interview Opinion On
        Health Assessment,Health Assessment Email Sent Date
        Health Assessment,Health Assessment Form Status
        Health Assessment,Health Assessment Submission Date
        Health Assessment,Health Assessment
        Health Assessment,Doctor Approval Decision
        Health Assessment,Doctor Approval decision date
        Non Sadhaka Stage: Review Stage,Ready For Review Date
        Non Sadhaka Stage: Review Stage,Reviewer Decision
        Non Sadhaka Stage: Review Stage,VRO/OCO Feedback Status
        Non Sadhaka Stage: Review Stage,Review Decision On
        Non Sadhaka Stage: Final Approval,Final Approval Decision Datetime
        Non Sadhaka Stage: Final Approval,Final Approver Decision
        Non Sadhaka Stage: Final Approval,Final Approval Form Status
        Non Sadhaka Stage: Final Approval,Final Approval Email Send Datetime
        SP Status: Ready for Onboarding,Arrival Email Sent Date
        SP Status: Ready for Onboarding,Arrival Batch
        SP Status: Ready for Onboarding,Arrival Status
        SP Status: Ready for Onboarding,Onboarding Status
        SP Status: Ready for Onboarding,Onboarding Call Status
        SP Status: Ready for Onboarding,Are you coming as couple?
        SP Status: Ready for Onboarding,Are you Coming with Laptop?
        SP Status: Ready for Onboarding,Mode of Travel
        SP Status: Ready for Onboarding,Verification Status
        SP Status: Ready for Onboarding,VMS Checkin Status
        SP Status: Ready for Onboarding,SP Epass Status
        SP Status: Ready for Onboarding,Arrival Datetime
        SP Status: Cancelled,Cancellation Date
        SP Status: Cancelled,Cancellation Reason
        SP Status: Cancelled,Previous Status
    '''))
    stage_to_status_mapping = dict()
    status_to_stage_mapping = dict()
    for row in range(sp_status_mapping_df.shape[0]):
        sp_status = sp_status_mapping_df['SP Status'].iloc[row]
        column_name = sp_status_mapping_df['Column'].iloc[row]
        if column_name in date_columns:
            continue
        stage_to_status_mapping[column_name] = sp_status
        if sp_status not in status_to_stage_mapping.keys():
            status_to_stage_mapping[sp_status] = [column_name]
        else:
            status_to_stage_mapping[sp_status].append(column_name)
    return stage_status_mappings, status_to_stage_mapping

def create_stage_counts_df(batch_df, non_date_columns, stage_to_status_mapping):
    stage_counts_dfs = []
    for stage in non_date_columns:
        stage_counts_df = batch_df[['SP ID'] + non_date_columns].groupby(stage, observed=False).size().reset_index().rename(columns={stage: 'Substage', 0: 'count'})
        stage_counts_df.insert(0,'Stage', stage)
        stage_counts_df.insert(0, 'SP Status',  stage_to_status_mapping[stage])
        stage_counts_dfs.append(stage_counts_df)
    stage_counts_df = pd.concat(stage_counts_dfs).reset_index(drop=True)
    return stage_counts_df

def create_status_tags_df(batch_df):
    # 'Arrival Tags' missing from target columns
    status_tags = ['Application Tags','Pre Registration Tags', 'Registration Tags', 'Interview Tags', 'Arrival Tags']
    status_tags_df = pd.DataFrame(columns=['Status Tag', 'Tag State', 'Count'])
    for status_tag in status_tags:
        status_tag_df = batch_df[['SP ID', status_tag]].groupby(status_tag).size().reset_index().rename(columns={status_tag: 'Tag State', 0: 'Count'})
        status_tag_df.insert(0, 'Status Tag', status_tag)
        status_tags_df = pd.concat([status_tags_df, status_tag_df])
    status_tags_df = status_tags_df.reset_index(drop=True)
    return status_tags_df

def create_dashboard(batch_df, date_columns_df, status_tags_df, date_col_counts_df, status_to_stage_mapping, stage_counts_df):
    app = dash.Dash(__name__)
    # app = JupyterDash(__name__)


    # ------------------------------------------------------------------------------
    # ------------- HTML LAYOUT AND SPECS FOR DASHBOARDS ---------------------------
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Dashboard Overview HTML
    # ------------------------------------------------------------------------------

    num_cancelations = batch_df[pd.notna(batch_df['Cancellation Date'])]['Cancellation Date'].shape[0]
    num_completed_apps = batch_df[pd.notna(batch_df['Final Approval Email Send Datetime'])]['Final Approval Email Send Datetime'].shape[0]
    num_apps = batch_df.shape[0]

    scorecard_style={
            "border": "1px solid #ddd",
            "border-radius": "8px",
            "padding": "20px",
            "width": "200px",     # Fixed width
            "height": "150px",    # Fixed height
            "textAlign": "center",
            "box-shadow": "2px 2px 12px rgba(0,0,0,0.1)",
            "display": "flex",
            "flex-direction": "column",
            "justify-content": "center",  # Center content vertically
            "align-items": "center",      # Center content horizontally
        }

    data_updated_until_scorecard = html.Div(
        children=[
            html.H4("Data Updated Until", style={"margin-bottom": "10px", "margin-top": "0px", 'fontSize': '18px'}),
            html.H5(f"{date_columns_df['Applied Date'].max().date()}", style={"margin": "0px", 'fontWeight': 'bold', 'fontSize': '32px'}),
        ],
        style=scorecard_style
    )

    total_upcoming_apps_scorecard = html.Div(
        children=[
            html.H4("Total Upcoming Applicants", style={"margin-bottom": "10px", "margin-top": "0px", 'fontSize': '18px'}),
            html.H5(f"{batch_df['SP ID'].unique().shape[0]}", style={"margin": "0px", 'fontWeight': 'bold', 'fontSize': '32px'}),
        ],
        style=scorecard_style
    )

    waiting_count_scorecard = html.Div(
        children=[
            html.H4("Waiting Applicants", style={"margin-bottom": "10px", "margin-top": "0px", 'fontSize': '18px'}),
            html.H5(f"{num_apps - num_completed_apps - num_cancelations}", style={"margin": "0px", 'fontWeight': 'bold', 'fontSize': '32px'}),
        ],
        style=scorecard_style
    )

    cancellation_count_scorecard = html.Div(
        children=[
            html.H4("Cancelled Applicants", style={"margin-bottom": "10px", "margin-top": "0px", 'fontSize': '18px'}),
            html.H5(f"{num_cancelations}", style={"margin": "0px", 'fontWeight': 'bold', 'fontSize': '32px'}),
        ],
        style=scorecard_style
    )

    completed_count_scorecard = html.Div(
        children=[
            html.H4("Completed Applicants", style={"margin-bottom": "10px", "margin-top": "0px", 'fontSize': '18px'}),
            html.H5(f"{num_completed_apps}", style={"margin": "0px", 'fontWeight': 'bold', 'fontSize': '32px'}),
        ],
        style=scorecard_style
    )

    dashboard_overview_html = [
        html.H1('SP Applications Dynamic Dashboards'),
        html.Div(
                [
                    data_updated_until_scorecard,
                    total_upcoming_apps_scorecard,
                    waiting_count_scorecard,
                    cancellation_count_scorecard,
                    completed_count_scorecard
                ],
                style={
                    'display': 'flex',
                    'justify-content': 'center',  # Centers scorecards horizontally
                    'align-items': 'center',      # Aligns the scorecards vertically
                    'gap': '20px',                # Space between scorecards
                }
            )
    ]

    # ------------------------------------------------------------------------------
    # Status Tags Table HTML
    # ------------------------------------------------------------------------------

    status_tags_html = [
        html.H1('SP Application Status Tags Counts'),
        dash_table.DataTable(
            id='status_tags_heatmap',
            columns=[{"name": i, "id": i} for i in status_tags_df.columns],
            data=status_tags_df.reset_index().to_dict('records'),
            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={'textAlign': 'center'},
            cell_selectable=True,
        ),
        html.Div(id='status_tags_user_ids'),
    ]

    # ------------------------------------------------------------------------------
    # Dated Stages Table HTML
    # ------------------------------------------------------------------------------

    dated_stages_table_description = """
    The table below shows the number of applicants in each cell which are currently
    waiting in the cells corresponding "Last Stage" row and "Wait Time" bucket in days.
    Ex. Last Stage: "Applied Date" and Wait Time: "1-10" days since applicant applied and
    has yet to move to the next stage of the application process. You can click on
    the cell to get the list of applicant SP ID's for that stage and wait time. You
    can also filter down those applicants with the drop down menus by first choosing
    what Substage They are in of the currently selected stage and what Subsubstage
    they are in of the now selected Substage.
    """
    dated_stages_html = [
        html.H1('SP Application Dated Columns - Wait Time'),
        html.P(dated_stages_table_description),
        dash_table.DataTable(
            id='dated_stages_heatmap',
            columns=[{"name": i, "id": i} for i in date_col_counts_df.columns.insert(0, 'Last Stage')],
            data=date_col_counts_df.reset_index().to_dict('records'),
            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={'textAlign': 'center'},
            cell_selectable=True,
        ),
        html.Div(id='user_ids'),
    ]

    # ------------------------------------------------------------------------------
    # Stage and Substage Table HTML
    # ------------------------------------------------------------------------------

    stage_substage_table_description = """
    Select a row in the table below of the Stage Substage pair you would like to
    get the SP ID's for. Use the two drop down menus to shrink the table to the
    desired SP Status and Stage columns that should be available. You can deselect
    both to get the full table of all Stage - Substage pairs (note this is a very
    large table.)
    """

    sp_status_dropdown_options = [
        {'label': status, 'value': status} for status in status_to_stage_mapping.keys()
    ]

    stages_default_options = [{'label': stage, 'value': stage} for stage in status_to_stage_mapping['Pre-registration']]
    substage_table_html = [
        html.H1('SP Application Stage Substage Table'),
        html.P(stage_substage_table_description),
        dcc.Dropdown(id='sp_status_dropdown', options=sp_status_dropdown_options, value='Pre-registration'),
        dcc.Dropdown(id='stage_dropdown', options=stages_default_options, value='Pre-Reg Call Status'),
        dash_table.DataTable(
            id='substage_heatmap',
            columns=[{"name": i, "id": i} for i in stage_counts_df.columns],
            data=stage_counts_df.reset_index().to_dict('records'),
            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={'textAlign': 'center'},
            cell_selectable=True,
        ),
        html.Div(id='substage_user_ids'),
    ]

    # Combine HTML modules into a single layout
    app.layout = html.Div(dashboard_overview_html + substage_table_html +
                        status_tags_html + dated_stages_html)


    # ------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------
    # ------------- DASHBOARD FEATURE CALL BACK FUNCTIONS --------------------------
    # ------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Stage and Substage Table Callbacks and utils
    # ------------------------------------------------------------------------------

    @app.callback(
        Output('stage_dropdown', 'options'),
        [Input('sp_status_dropdown', 'value')]
    )
    def update_dropdown(sp_status_selected):
        if sp_status_selected:
            stages = status_to_stage_mapping[sp_status_selected]
            return [{'label': stage, 'value': stage} for stage in stages]
        else:
            return [{'label': 'nothing', 'value': 'nothing'}]

    @app.callback(
        Output('substage_heatmap', 'data'),
        [Input('sp_status_dropdown', 'value'),
        Input('stage_dropdown', 'value')]
    )
    def update_dropdown(sp_status_selected, stage):
        if sp_status_selected and stage:
            return stage_counts_df[(stage_counts_df['SP Status']==sp_status_selected) & (stage_counts_df['Stage']==stage)].reset_index().to_dict('records')
        else:
            return stage_counts_df.reset_index().to_dict('records')

    @app.callback(
        Output('substage_user_ids', 'children'),
        [Input('substage_heatmap', 'active_cell'),
        Input('sp_status_dropdown', 'value'),
        Input('stage_dropdown', 'value')]
    )
    def display_substage_user_ids(active_cell, sp_status, stage):
        if active_cell and sp_status and stage:
            substage = stage_counts_df[(stage_counts_df['SP Status']==sp_status) & (stage_counts_df['Stage']==stage)]['Substage'].reset_index(drop=True).iloc[active_cell['row']]
            selected_users = batch_df[batch_df[stage]==substage]['SP ID'].unique()
            selected_users_str = ','.join(selected_users)
            return html.Pre(f"User IDs in {stage} - {substage}:\n{selected_users_str}")
        elif active_cell:
            stage = stage_counts_df['Stage'].iloc[active_cell['row']]
            substage = stage_counts_df['Substage'].iloc[active_cell['row']]
            selected_users = batch_df[batch_df[stage]==substage]['SP ID'].unique()
            selected_users_str = ','.join(selected_users)
            return html.Pre(f"\nUser IDs in {stage} - {substage}:\n{selected_users_str}")
        return "\nClick on a cell to see the user IDs."


    # ------------------------------------------------------------------------------
    # Status Tags Callbacks and utils
    # ------------------------------------------------------------------------------

    # Callback to output user ids based on clicked cell
    @app.callback(
        Output('status_tags_user_ids', 'children'),
        [Input('status_tags_heatmap', 'active_cell')]
    )
    def display_status_tags_user_ids(active_cell):
        if active_cell:
            row = active_cell['row']
            status_tag = status_tags_df['Status Tag'].iloc[row]
            tag_state = status_tags_df['Tag State'].iloc[row]
            selected_users = batch_df['SP ID'][batch_df[status_tag]==tag_state].unique()
            selected_users_str = ','.join(selected_users)
            return html.Pre(f"User IDs in {status_tag} - {tag_state}:\n{selected_users_str}")

        return "Click on a cell to see the user IDs."

    # ------------------------------------------------------------------------------
    # Dated Stages Table Callbacks and utils
    # ------------------------------------------------------------------------------

    # Callback to output user ids based on clicked cell
    @app.callback(
        Output('user_ids', 'children'),
        [Input('dated_stages_heatmap', 'active_cell')]
    )
    def display_user_ids(active_cell):
        if active_cell:
            stage = date_col_counts_df.index[active_cell['row']]
            wait_bin = date_col_counts_df.columns[active_cell['column'] - 1]
            selected_users = date_columns_df[(date_columns_df['Last Stage'] == stage) & (date_columns_df['Wait Time Bucket'] == wait_bin)].index.tolist()
            selected_users_str = ','.join(map(str, selected_users))
            return html.Pre(f"User IDs in {stage} {wait_bin}:\n{selected_users_str}")
        return "Click on a cell to see the user IDs."

    return app

    # There are three options right now for generating the dashboard html

    # ----------------------------------------------------
    # Option 1: Dash jupyter mode
    # This will create a localhost link and has suspect support from Colab due to
    # security features that may change
    # ----------------------------------------------------
    # app.run(jupyter_mode="external")


    # ----------------------------------------------------
    # Option 2: Link framing this juptyer cells frame?
    # ----------------------------------------------------
    # def get_colab_link(port):
    #     from google.colab.output import eval_js
    #     return eval_js(f"google.colab.kernel.proxyPort({port})")
    # # Display the public URL generated by Colab
    # print(f'Dashboard should be accessible at this URL: {get_colab_link(8050)}')
    # # Run the Dash app on port 8050
    # app.run_server(port=8050, debug=False, use_reloader=False)

    # ----------------------------------------------------
    # Option 3: Run from JupyterDash
    # This might be deprecated in the future though
    # ----------------------------------------------------
    # note need to change: app = JupyterDash(__name__)
    # and add: from jupyter_dash import JupyterDash
    # app.run_server(mode='external')

    # ----------------------------------------------------
    # Option 4: Run locally in colab displaying in the console below
    # ----------------------------------------------------
    # Run Locally in Colab cell
    #app.run_server(debug=False)

    # ----------------------------------------------------
    # Option 5: Run locally in colab displaying in the console below
    # ----------------------------------------------------

    # ----------------------------------------------------
    # Option 6: Run on a third party service like ngrok
    # ----------------------------------------------------

