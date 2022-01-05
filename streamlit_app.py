# IMPORTS --------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# OPTIONS --------------------------------------------------------------------------------

## Yes, I am using rename() every time I want to display a dataframe
## as I didn't want to refactor everything

pd.set_option('display.max_colwidth', None)

st.set_page_config(
    page_title="SD Dashboard",
    page_icon=":football:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CLEANING FUNC ------------------------------------------------------------------------------

@st.cache
def cleanData(df):
    '''
    Cleans a raw DraftKings NFL Showdown contest CSV.

            Parameters:
                    df (pandas DataFrame): Raw DraftKings NFL Showdown contest

            Returns:
                    df (pandas DataFrame): Cleaned DraftKings NFL Showdown contest
    '''

    df = df.drop(['Rank', 'EntryId', 'TimeRemaining', 'Points','Unnamed: 6', 'Player', 'Roster Position', '%Drafted', 'FPTS'], axis = 1)

    df['entry_new'] = df['EntryName'].str.split(' ').str[0]
    
    df = df.dropna()
    
    df['unique'] = df['Lineup'].map(df.groupby("Lineup").count()['entry_new'] == 1).astype(int)
    
    df['dupes'] = df.groupby('Lineup')['Lineup'].transform('count')
    
    df['user_entries'] = df['EntryName'].str.extract(r"\((.*?)\)", expand=False)
    
    df['user_entries'] = df['user_entries'].str.split('/').str[1]
    
    df.user_entries = df.user_entries.fillna(1)
    
    df['user_uniques'] = df.groupby('entry_new')['unique'].transform('sum')

    df['<10_dupes'] = (df['dupes'] < 10).groupby(df['entry_new']).transform('sum')
    
    df = df.drop(['EntryName'], axis=1)

    df['user_entries'] = df['user_entries'].astype(int)

    df['unique%'] = round((df['user_uniques'] / df['user_entries']) * 100,2)
  
    df=df.rename(columns={'entry_new':'user','Lineup':'lineup'})

    split = df.lineup.str.split('FLEX|CPT',expand=True)
     
    # df = (pd
    # .merge(df, split, left_index=True, right_index=True)
    # .rename(columns={1:'CPT', 2:'FLEX1', 3:'FLEX2', 4:'FLEX3', 5:'FLEX4', 6:'FLEX5'})
    # .drop([0],axis=1)
    # )

    # this logic allows old contest CSV to work in the app (CPT used to be listed last)
    if (df.lineup.str[:3] == 'CPT').all():
        df = (pd
        .merge(df, split, left_index=True, right_index=True)
        .rename(columns={1:'CPT', 2:'FLEX1', 3:'FLEX2', 4:'FLEX3', 5:'FLEX4', 6:'FLEX5'})
        .drop([0],axis=1)
        )

    elif (df.lineup.str[:3] == 'FLE').all():
        df = (pd
        .merge(df, split, left_index=True, right_index=True)
        .rename(columns={1:'FLEX1', 2:'FLEX2', 3:'FLEX3', 4:'FLEX4', 5:'FLEX5', 6:'CPT'})
        .drop([0],axis=1)
        )

    cols = ['FLEX1','FLEX2','FLEX3','FLEX4','FLEX5','CPT']
    
    for i in cols:
        df[i] = df[i].str.rstrip().str.lstrip()

    df['FLEX'] = df.FLEX1 + ', ' + df.FLEX2 + ', ' + df.FLEX3 + ', ' + df.FLEX4 + ', ' + df.FLEX5
        
    df=df[
        ['user','user_entries','user_uniques','<10_dupes',
        'unique%','lineup','unique','dupes','FLEX','CPT']
        ]
    
    return df

# TITLE --------------------------------------------------------------------------------

st.title('NFL Showdown Dashboard')

st.markdown("---")

# MAIN PART OF SCRIPT ------------------------------------------------------------------

# file uploader
uploaded_file = st.sidebar.file_uploader("Upload a DraftKings Showdown Contest CSV")

# if a file has been uploaded
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)

    # try the following
    try:
        if ['Rank', 'EntryId', 'EntryName', 'TimeRemaining', 'Points', 'Lineup',
       'Unnamed: 6', 'Player', 'Roster Position', '%Drafted', 'FPTS'] == list(data.columns):

            players = list(set(data.Player.dropna()))

            @st.cache
            def getfieldExposure(df,players=players):
                '''
                Calculates the roster rate of each player 
                on the slate for the entire field.

                        Parameters:
                                df (pandas DataFrame): 
                                players (list): List of players on the slate

                        Returns:
                                exps (dict): Dictionary of player 
                                roster rates for the entire field
                '''

                exps = {
                'Player':players,
                'CPT':[],
                'FLEX':[]
                }

                for i in exps['Player']:
                    exps['CPT'].append(
                        (len(df.loc[df.CPT.str.contains(i)])) / len(df) * 100
                        )
                    exps['FLEX'].append(
                        (len(df.loc[df.FLEX.str.contains(i)])) / len(df) * 100
                    )

                return exps

            @st.cache
            def getuserExposure(user, df, players=players):
                '''
                Calculates the roster rate of each player 
                on the slate for a given user.

                        Parameters:
                                user (str): String of the user to be analyzed
                                df (pandas DataFrame): 
                                players (list): List of players on the slate

                        Returns:
                                userExps (dict): Dictionary of player 
                                roster rates for the given user
                '''

                userExps = {
                'Player':players,
                f'{user}_FLEX':[],
                f'{user}_CPT':[]
                }

                userDf = df.loc[df.user==user].copy()

                for i in userExps['Player']:
                    userExps[f'{user}_FLEX'].append(
                        (len(userDf.loc[userDf.FLEX.str.contains(i)])) / len(userDf) * 100
                        )
                    userExps[f'{user}_CPT'].append(
                        (len(userDf.loc[userDf.CPT.str.contains(i)])) / len(userDf) * 100
                        )
                    userExps[f'{user}_Lineups'] = len(userDf)

                return userExps

            df = cleanData(data)
            df_ = df.copy()

            select = st.sidebar.radio('Analysis',
            ('Slate-Wide Stats',
            'Individual User Stats',
            'User Exposure Comparison',
            'Player Combination Queries',
            'Player Combination Visualizer'))
            st.subheader(select)

            if select == 'Slate-Wide Stats':

                st.write("*If any of the dataframes are truncated, closing the sidebar may help.*")

                col1, col2 = st.columns([1,1.5])

                with col1:
                    exposures = pd.DataFrame(getfieldExposure(df_))

                    exposures['TOTAL'] = exposures['CPT'] + exposures['FLEX']

                    exposures = (exposures
                    .loc[exposures.TOTAL > .99]
                    .round(decimals=2)
                    .sort_values('TOTAL',ascending=False)
                    .reset_index(drop=True))

                    st.caption('Roster Rates (discarding blank lineups)')

                    st.dataframe((exposures
                    .style
                    .background_gradient(cmap='RdYlBu')
                    .set_precision(2)),
                    width=2000,
                    height=1000)

                with col2:
                    leaders = (df_
                    .iloc[:,:-5]
                    .drop_duplicates(subset=['user'])
                    .sort_values(by=['user_uniques'], ascending= False)
                    .reset_index(drop=True)
                    .head(25))

                    st.caption('User Unique Leaders')

                    st.dataframe((leaders
                    .rename(columns={
                        'user':'User','user_entries':'Entries','user_uniques':'Uniques',
                        '<10_dupes':'u10Dupes','unique%':'Unique%'
                        })
                    .style
                    .background_gradient(cmap='RdYlBu')
                    .set_precision(2)),
                    width=1500,
                    height=1000)

                chalk = (df_
                .drop_duplicates(subset=['lineup'])
                .sort_values(by=['dupes'], ascending= False)
                .reset_index(drop=True)
                .head(20))

                st.caption('Chalk Lineups')

                st.dataframe((chalk[['FLEX','CPT','dupes']]
                .rename(columns={'dupes':'Dupes'})
                .style
                .background_gradient(cmap='RdYlBu')),
                height=1000,
                width=1500)

            elif select == 'Individual User Stats':
                option = st.selectbox(
                'Select a User',
                pd.Series(sorted(df_.user.drop_duplicates()))
                )

                userDf = (df_
                .loc[df_.user==option]
                .sort_values(by='dupes')
                .reset_index(drop=True))

                st.markdown(f'### `{userDf.user_entries.max()}` User Entries, ' \
                            f'`{userDf.user_uniques.max()}` Uniques, ' \
                            f'`{userDf["<10_dupes"].max()}` u10 Dupes, ' \
                            f'`{round((userDf["user_uniques"].max() / userDf.user_entries.median()) * 100,2)}` ' \
                                'Unique Percentage')

                st.write("*If any of the dataframes are truncated, closing the sidebar may help.*")

                # st.table((pd.DataFrame(
                #     {
                #         'User Entries': [userDf.user_entries.max()],
                #         'User Uniques': [userDf.user_uniques.max()],
                #         'Less than 10 Dupes': [userDf["<10_dupes"].max()],
                #         'Unique Percentage': [userDf["user_uniques"].max() / userDf.user_entries.max()]
                #     })
                #     .style
                #     .set_precision(2))
                #     )

                st.dataframe((userDf
                [['FLEX','CPT','unique','dupes']]
                .rename(columns={'unique':'Unique','dupes':'Dupes'})
                .style
                .background_gradient(cmap='RdYlBu_r',subset='Dupes')
                .set_precision(2)),
                height=1200,
                width=1500)

            elif select == 'User Exposure Comparison':
                comp1 = st.selectbox(
                'Select a User',
                pd.Series(sorted(df_.user.drop_duplicates()))
                )

                s = pd.Series(sorted(df_.user.loc[df_.user != comp1].drop_duplicates()))
                s.index = s.index+1
                s = pd.concat([pd.Series('Field'),s])

                comp2 = st.selectbox(
                'Select another User (or the field)',
                s
                )

                st.write("*If any of the dataframes are truncated, closing the sidebar may help.*")

                if comp2 == 'Field':
                    compFLEX = (pd
                    .DataFrame(getuserExposure(comp1,df_))
                    .merge(pd.DataFrame(getfieldExposure(df_)), on='Player')
                    .rename(columns={'CPT':f'{comp2}_CPT','FLEX':f'{comp2}_FLEX'})
                    [['Player',f'{comp1}_FLEX',f'{comp2}_FLEX']]
                    )

                    compFLEX['Diff'] = compFLEX[f'{comp1}_FLEX'] - compFLEX[f'{comp2}_FLEX']

                    compFLEX = (compFLEX
                    .loc[
                        (
                            ~(
                                (compFLEX[f'{comp1}_FLEX'] == 0) & 
                                (compFLEX[f'{comp2}_FLEX'] == 0)
                                )) &
                            (
                                (compFLEX[f'{comp2}_FLEX'] > 1.0) |
                                (compFLEX[f'{comp1}_FLEX'] > 0))
                            ])

                    compCPT = (pd
                    .DataFrame(getuserExposure(comp1,df_))
                    .merge(pd.DataFrame(getfieldExposure(df_)), on='Player')
                    .rename(columns={'CPT':f'{comp2}_CPT','FLEX':f'{comp2}_FLEX'})
                    [['Player',f'{comp1}_CPT',f'{comp2}_CPT']]
                    )

                    compCPT['Diff'] = compCPT[f'{comp1}_CPT'] - compCPT[f'{comp2}_CPT']

                    compCPT = (compCPT
                    .loc[
                        (
                            ~(
                                (compCPT[f'{comp1}_CPT'] == 0) & 
                                (compCPT[f'{comp2}_CPT'] == 0)
                                )) &
                            (
                                (compCPT[f'{comp2}_CPT'] > 1.0) |
                                (compCPT[f'{comp1}_CPT'] > 0))
                            ])

                else:
                    compFLEX = (pd
                    .DataFrame(getuserExposure(comp1,df_))
                    .merge(pd.DataFrame(getuserExposure(comp2,df_)), on='Player')
                    [['Player',f'{comp1}_FLEX',f'{comp2}_FLEX']]
                    )

                    compFLEX['Diff'] = compFLEX[f'{comp1}_FLEX'] - compFLEX[f'{comp2}_FLEX']

                    compFLEX = (compFLEX
                    .loc[
                        ~(
                            (compFLEX[f'{comp1}_FLEX'] == 0) & 
                            (compFLEX[f'{comp2}_FLEX'] == 0)
                            )
                            ])

                    compCPT = (pd
                    .DataFrame(getuserExposure(comp1,df_))
                    .merge(pd.DataFrame(getuserExposure(comp2,df_)), on='Player')
                    [['Player',f'{comp1}_CPT',f'{comp2}_CPT']]
                    )

                    compCPT['Diff'] = compCPT[f'{comp1}_CPT'] - compCPT[f'{comp2}_CPT']

                    compCPT = compCPT.loc[~((compCPT[f'{comp1}_CPT'] == 0) & (compCPT[f'{comp2}_CPT'] == 0))]

                col1, col2 = st.columns(2)

                with col1:
                    st.dataframe((compFLEX
                    .sort_values(by='Diff', ascending=False)
                    .reset_index(drop=True)
                    .style
                    .background_gradient(cmap='RdYlBu',subset='Diff')
                    .set_precision(2)),
                    height=1200)

                with col2:
                    st.dataframe((compCPT
                    .sort_values(by='Diff', ascending=False)
                    .reset_index(drop=True)
                    .style
                    .background_gradient(cmap='RdYlBu',subset='Diff')
                    .set_precision(2)),
                    height=1200)

                if comp2 == 'Field':
                    pass
                
                else:
                    comp = (pd
                    .DataFrame(getuserExposure(comp1,df_))
                    .merge(pd.DataFrame(getuserExposure(comp2,df_)), on='Player')
                    )

                    st.dataframe((comp
                    .loc[~(
                            (comp[f'{comp1}_FLEX'] == 0) &
                            (comp[f'{comp1}_CPT'] == 0) &
                            (comp[f'{comp2}_FLEX'] == 0) &
                            (comp[f'{comp2}_CPT'] == 0)
                            )
                        ]
                    .style
                    .set_precision(2))
                    )

            elif select == 'Player Combination Queries':
                
                exposures__ = pd.DataFrame(getfieldExposure(df_))
                exposures__['TOTAL'] = exposures__['CPT'] + exposures__['FLEX']

                playersLst = sorted(list(exposures__.loc[exposures__.TOTAL>.99,'Player']))

                col1, col2 = st.columns(2)

                with col1:
                    player1 = st.selectbox(
                        'Select a Player',
                        sorted(playersLst)
                        )

                    player1Pos = st.selectbox(
                        'CPT or FLEX?',
                        ('CPT','FLEX'),
                        key = 'player1Pos'
                    )

                with col2:
                    player2 = st.selectbox(
                        'Select another Player',
                        pd.Series(sorted(playersLst)).loc[pd.Series(sorted(playersLst)) != player1]
                        )

                    player2Pos = st.selectbox(
                        'CPT or FLEX?',
                        ('FLEX','CPT'),
                        key = 'player2Pos'
                        )
                    
                # if player1Pos and player2Pos == 'CPT':
                #     st.error("You can't have 2 CPTs in one lineup.")
                #     st.stop()

                # else:

                #     query = df_.loc[
                #         (df_[f'{player1Pos}'].str.contains(player1)) &
                #         (df_[f'{player2Pos}'].str.contains(player2))
                #         ]
 
                #     st.markdown(f'### There are `{len(query)}` lineups with {player1} {player1Pos} ' \
                #              f'and {player2} {player2Pos} `({round((len(query) / len(df_)) * 100,2)}%)`. ' \
                #              f'`{query.unique.sum()}` are unique.')

                query = df_.loc[
                        (df_[f'{player1Pos}'].str.contains(player1)) &
                        (df_[f'{player2Pos}'].str.contains(player2))
                        ]
 
                st.markdown(f'### There are `{len(query)}` lineups with {player1} {player1Pos} ' \
                        f'and {player2} {player2Pos} `({round((len(query) / len(df_)) * 100,2)}%)`. ' \
                        f'`{query.unique.sum()}` are unique.')

                    # st.table((pd.DataFrame(
                    # {
                    #     'Combo': [f'{player1} {player1Pos}, {player2} {player2Pos}'],
                    #     'Lineups': [len(query)],
                    #     'Percent of All Lineups': [round((len(query) / len(df_)) * 100,2)],
                    #     'Unique': [query.unique.sum()]
                    # })
                    # .style
                    # .set_precision(2))
                    # )

                st.write("*If the dataframe is truncated, closing the sidebar may help.*")
                filt = (df_
                .loc[
                    (df_[f'{player1Pos}'].str.contains(player1)) &
                    (df_[f'{player2Pos}'].str.contains(player2))
                    ]
                .sort_values(by='dupes',ascending=False)
                .drop_duplicates(subset=['lineup'])
                .reset_index(drop=True))

                st.dataframe((filt[['FLEX','CPT','unique','dupes']]
                .rename(columns={'unique':'Unique','dupes':'Dupes'})
                .style
                .background_gradient(cmap='RdYlBu',subset='Dupes')
                .set_precision(2)),
                height=1200,
                width=1500)

            elif select == 'Player Combination Visualizer':
                st.caption('This heatmap shows the percentage of all lineups that had a certain CPT and FLEX pairing. ' \
                           'Only players with 5% or more total ownership are included on this chart.')

                dfCorr = df.copy()
                exposures_ = pd.DataFrame(getfieldExposure(df_))

                @st.cache
                def corrPlot(exposures_, dfCorr):
                    exposures_['TOTAL'] = exposures_['CPT'] + exposures_['FLEX']
                    playerCorr = list(set(exposures_.loc[exposures_.TOTAL>5,'Player']))
                    playerCorr = [i.strip() for i in playerCorr]
                    
                    cpt_ = dfCorr.lineup.str.partition(" FLEX")[0]
                    dfCorr.lineup = dfCorr.lineup.str.partition(" FLEX")[2] + ' ' + cpt_

                    flex = dfCorr['lineup'].str.split('FLEX|CPT', expand = True)

                    flex.columns = ['FLEX1', 'FLEX2', 'FLEX3', 'FLEX4', 'FLEX5', 'CPT']

                    flex= flex[['FLEX1', 'FLEX2', 'FLEX3', 'FLEX4', 'FLEX5', 'CPT']]

                    flex['id'] = flex.index

                    keys = [c for c in flex if c.startswith('FLEX')]

                    cpts = pd.melt(flex, id_vars='CPT', value_vars=keys, value_name='FLEX')
                    cpts = cpts.dropna()

                    cpts['CPT'] = cpts['CPT'].str.strip()
                    cpts['CPT'] = cpts['CPT'].astype('category')
                    cpts['FLEX'] = cpts['FLEX'].str.strip()
                    cpts['FLEX'] = cpts['FLEX'].astype('category')

                    cpts = cpts.loc[(
                        (cpts.CPT.isin(playerCorr)) & 
                        (cpts.FLEX.isin(playerCorr)))]

                    m = pd.crosstab(cpts["CPT"], cpts["FLEX"])
                    m = pd.crosstab(cpts["CPT"], cpts["FLEX"])
                    m_div = m.div(len(dfCorr), axis=0)

                    return m_div

                heatmap = corrPlot(exposures_, dfCorr)

                fig, ax = plt.subplots(figsize=(6,6))
                hm = sns.heatmap(heatmap, cmap='RdYlBu',fmt='.2f')
                ax.tick_params(labelsize=6)
                cax = plt.gcf().axes[-1]
                cax.tick_params(labelsize=8)

                st.pyplot(fig)

        # if a file is correctly read but is not an NFL Showdown CSV
        else:
            st.error("Hmm... We don't think this is a a DraftKings Showdown Contest CSV. " \
                        "Please double check and try again.")
            st.stop()

    # if there is an error in reading the file
    except KeyError:
        st.error('Sorry, an error has occurred. We currently only have functionality for NFL Shodown contests. ' \
                 'Are you sure the CSV you uploaded is an NFL contest?')
        st.stop()

    except ValueError:
        st.error('Sorry, an error has occurred. We currently only have functionality for NFL Shodown contests. ' \
                 'Are you sure the CSV you uploaded is an NFL contest?')
        st.stop()

# if a file hasn't been uploaded yet
else:

    st.markdown("### Welcome to the NFL Showdown Dashboard! " \
                "Please upload a Showdown contest CSV via the expander tab on the left.\n" \
                "#### Not sure where to find a contest CSV?\n" \
                "1. Go to the DraftKings site (desktop version)\n" \
                "2. Open up any LIVE contest page\n" \
                "3. In the bottom left, click `Export Lineups as CSV`\n" \
                "4. Unzip the file and the you should see the CSV!\n\n")
                
    st.markdown("#### Don't have a DraftKings account? Click the button below for a sample contest CSV.")

    _csv = pd.read_csv('sampleContest.csv')
    csv = _csv.to_csv(index=False).encode('utf-8')
    st.download_button(
     label="Download a sample contest (1.3 MB)",
     data=csv,
     file_name='sampleContest.csv',
     mime='text/csv',
 )

    st.markdown("#### Enjoy the app? \n" \
                "##### If this app is beneficial to you and you're feeling generous, **_my venmo is `@bolg23`_**"
    )

    st.markdown("###### **_NOTE: This will NOT work with Classic mode for various reasons. " \
                "Please refrain from uploading a Classic mode CSV to this web app._**")

# MORE INFO EXPANDER --------------------------------------------------------------

with st.sidebar.expander("More Info"):
    st.write("""
         This web app runs analyses on DraftKings NFL Showdown contests.

        \n
         - **Slate-Wide Stats**
            - Exposures - Roster Rates for each player on the slate (FLEX, CPT, and TOTAL)
                - Discarding blank lineups (decimal values might be slightly different than what DK shows)
            - User Unique Leaders - Which users had the most unique lineups, highest unique lineup rate, etc.
            - Chalk Lineups - Which lineups were duplicated the most?

        \n
        - **Individual User Stats**
            - Complete user lineup statistics, filterable by any user who entered the slate

        \n
        - **User/Field Exposure Comparison**
            - Comparison of user/field exposures for both FLEX and CPT filterable by any two users who entered the slate (or the field)
            - `Diff` column is with respect to the first user selected (User1 - User2)

        \n
        - **Player Combo Queries**
            - Takes any 2 player CPT/FLEX combo and calculates popular and unique it is
            - Only players with a roster rate greater than .99% are included

        \n
        - **Player Combination Visualizer**
            - A heatmap showing all CPT/FLEX combos for players with more than a 5% total roster rate
            - Shows the percentage of all lineups that had a certain CPT and FLEX pairing
     """)