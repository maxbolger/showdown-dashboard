# [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/maxbolger/showdown-dashboard/main)

# DraftKings NFL Showdown Dashboard

This web app runs analyses on DraftKings NFL Showdown contests.


- **Slate-Wide Stats**
   - Exposures - Roster Rates for each player on the slate (FLEX, CPT, and TOTAL)
       - Discarding blank lineups (decimal values might be slightly different than what DK shows)
   - User Unique Leaders - Which users had the most unique lineups, highest unique lineup rate, etc.
   - Chalk Lineups - Which lineups were duplicated the most?


- **Individual User Stats**
   - Complete user lineup statistics, filterable by any user who entered the slate


- **User/Field Exposure Comparison**
   - Comparison of user/field exposures for both FLEX and CPT filterable by any two users who entered the slate (or the field)
   - `Diff` column is with respect to the first user selected (User1 - User2)


- **Player Combo Queries**
   - Takes any 2 player CPT/FLEX combo and calculates popular and unique it is
   - Only players with a roster rate greater than .99% are included


- **Player Combination Visualizer**
   - A heatmap showing all CPT/FLEX combos for players with more than a 5% total roster rate
   - Shows the percentage of all lineups that had a certain CPT and FLEX pairing

### **Click the badge above or [CLICK HERE](https://share.streamlit.io/maxbolger/showdown-dashboard/main) to visit the app!**


### By: Max Bolger [@mnpykings](https://twitter.com/mnpykings), 2020
