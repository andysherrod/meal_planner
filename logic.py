import calendar
import pandas as pd
from datetime import timedelta

def get_category_days(year, month, category, end_date=None):
    """Counts valid days for a category in a given month, up to an optional end_date."""
    cal = calendar.Calendar()
    days = 0
    for day in cal.itermonthdates(year, month):
        if day.month == month:
            # Stop counting if we reach the end_date
            if end_date and day >= end_date:
                continue
            
            # Tally up the days based on keywords in the category name
            cat_name = category.lower()
            if 'weekday' in cat_name and day.weekday() < 5: # 0-4 is Mon-Fri
                days += 1
            elif 'weekend' in cat_name and day.weekday() >= 5: # 5-6 is Sat-Sun
                days += 1
            elif 'weekday' not in cat_name and 'weekend' not in cat_name: # Everyday categories
                days += 1
    return days

def calculate_dashboard_stats(current_date, budgets, df):
    year = current_date.year
    month = current_date.month
    
    # Identify the start of the current week (Monday)
    week_start = current_date - timedelta(days=current_date.weekday())
    
    # Ensure our math doesn't look at the previous month if week 1 starts late
    month_start = current_date.replace(day=1)
    effective_week_start = max(week_start, month_start)
    
    stats = {}
    
    # Standardize the date column if dataframe isn't empty
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    for cat, total_budget in budgets.items():
        total_days = get_category_days(year, month, cat)
        days_passed = get_category_days(year, month, cat, end_date=effective_week_start)
        
        # Calculate spending from past weeks and the current week
        if not df.empty:
            past_mask = (df['Category'] == cat) & (df['Date'] < effective_week_start) & (df['Date'] >= month_start)
            past_spend = df.loc[past_mask, 'Amount'].sum()
            
            week_mask = (df['Category'] == cat) & (df['Date'] >= effective_week_start) & (df['Date'] <= current_date)
            week_spend = df.loc[week_mask, 'Amount'].sum()
        else:
            past_spend = 0
            week_spend = 0
            
        # The Weekly Adjustment Math
        remaining_budget = total_budget - past_spend
        remaining_days = total_days - days_passed
        
        daily_target = remaining_budget / remaining_days if remaining_days > 0 else 0
        
        # Calculate the budget for specifically this current week
        next_week_start = week_start + timedelta(days=7)
        days_this_week = get_category_days(year, month, cat, end_date=next_week_start) - days_passed
        
        weekly_budget = daily_target * days_this_week
        weekly_remaining = weekly_budget - week_spend
        
        stats[cat] = {
            'daily_target': daily_target,
            'weekly_remaining': weekly_remaining,
            'week_spend': week_spend
        }
        
    return stats
