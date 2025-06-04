import pandas as pd
import os
from datetime import datetime
import shutil
import math
from docx import Document
import warnings
import glob

TESTING_MODE = False  # Change to True to enable testing mode
TOTAL_SCHOOL_DAYS = 160  # as of (date)

def clear_old_csvs_in_all_buildings(base_output_path, building_group_mapping):
    """
    Clears all old CSV files in the directories for each building group.
    
    Args:
    - base_output_path (str): The base directory where the building folders are located.
    - building_group_mapping (dict): A dictionary mapping building groups to lists of school names.
    
    Returns:
    - None
    """
    output_path = get_output_dir(base_output_path, TESTING_MODE)

    for group_name in building_group_mapping.keys():
        building_path = os.path.join(output_path, group_name)
        
        # Check if the directory exists and clear the old CSVs if it does
        if os.path.exists(building_path):
            csv_files = glob.glob(os.path.join(building_path, '*.csv'))
            for csv_file in csv_files:
                os.remove(csv_file)
                print(f"Deleted old CSV file: {csv_file}")

    # Also handle the Uncategorized folder if needed
    uncategorized_path = os.path.join(output_path, 'Uncategorized')
    if os.path.exists(uncategorized_path):
        csv_files = glob.glob(os.path.join(uncategorized_path, '*.csv'))
        for csv_file in csv_files:
            os.remove(csv_file)
            print(f"Deleted old CSV file: {csv_file}")

def add_attendance_category(results):
    """
    Adds a new 'attendance_category' field to the results dictionary based on current_week_att_percent.
    
    Args:
    - results (dict): The dictionary containing attendance data for students.
    
    Returns:
    - dict: The updated dictionary with the new 'attendance_category' field.
    """
    
    def categorize_attendance(att_percent):
        """Categorizes attendance percentage into the defined groups."""
        if att_percent < 85:
            return 'Below 85'
        elif 85 <= att_percent < 87.5:
            return '85 to below 87.5'
        elif 87.5 <= att_percent < 90:
            return '87.5 to below 90'
        elif 90 <= att_percent < 94:
            return '90 to below 94'
        else:
            return '94 and above'
    
    # Loop through the results and add the attendance category
    for student_id, data in results.items():
        current_week_att_percent = data.get('current_week_att_percent')
        if current_week_att_percent is not None:
            # Add the attendance category to the results
            results[student_id]['attendance_category'] = categorize_attendance(current_week_att_percent)
    
    return results


def read_csv(file_path, column_mapping):
    """
    Reads a CSV file and renames columns based on the provided column mapping.

    Args:
    - file_path (str): The path to the CSV file.
    - column_mapping (dict): A dictionary mapping old column names to new standardized column names.

    Returns:
    - DataFrame: A DataFrame with renamed columns.
    """
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        df = df.rename(columns=column_mapping)
        
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
        return pd.DataFrame() # Return an empty DataFrame if the file is not found
    except Exception as e:
        print(f"An error occurred while reading the file {file_path}: {e}")
        return pd.DataFrame() # Return an empty DataFrame if an error occurs
    
    return df

#Function to convert a data frame to a dict
def df_to_dict(df):
    """
    Converts a DataFrame to a list of dictionaries, where each dictionary represents a row in the DataFrame.

    Args:
    - df (DataFrame): The DataFrame to convert.

    Returns:
    - list: A list of dictionaries with the DataFrame's data.
    """
    dict_data = df.to_dict(orient='records')
    
    return dict_data

def prepare_current_week_data(current_week_data):
    """
    Prepares the current week's data by converting it to a DataFrame and setting the weekly value to -1.

    Args:
    - current_week_data (list): A list of dictionaries containing the current week's attendance data.

    Returns:
    - DataFrame: A DataFrame with the current week's data and the weekly value set to -1.
    """
    df = pd.DataFrame(current_week_data)
    df['weekly_value'] = -1
    return df

def base_file_exists(base_file_path):
    """
    Checks if the base file exists.

    Args:
    - base_file_path (str): The path to the base file.

    Returns:
    - bool: True if the base file exists, False otherwise.
    """
    exists = os.path.exists(base_file_path)
    
    return exists

def initialize_base_file(current_week_data, base_file_path):
    """
    Initializes the base file with the current week's data.

    Args:
    - current_week_data (list): A list of dictionaries containing the current week's attendance data.
    - base_file_path (str): The path to the base file.

    Returns:
    - None
    """
    df = prepare_current_week_data(current_week_data)
    df.to_csv(base_file_path, index=False)

def clean_base_file(df):
    """
    Removes records with a weekly value of -3 from the DataFrame.

    Args:
    - df (DataFrame): The DataFrame to clean.

    Returns:
    - DataFrame: A cleaned DataFrame with records having weekly value of -3 removed.
    """
    cleaned_df = df[df['weekly_value'] != -3]
    return cleaned_df

def update_base_file(current_week_data, base_file_path, column_mapping):
    """
    Updates the base file by decrementing the weekly values and adding the current week's data.

    Args:
    - current_week_data (list): A list of dictionaries containing the current week's attendance data.
    - base_file_path (str): The path to the base file.
    - column_mapping (dict): A dictionary mapping old column names to new standardized column names.

    Returns:
    - None
    """

    # If testing mode is enabled, skip the base file update
    if TESTING_MODE:
        print("Testing mode is ON. Skipping base file update.")
        return
    
    if not base_file_exists(base_file_path):
        initialize_base_file(current_week_data, base_file_path)
        return
    
    # Create a backup of the existing base file
    create_backup(base_file_path)

    df = read_csv(base_file_path, column_mapping) 
    # Decrement weekly values
    df['weekly_value'] = df['weekly_value'] - 1
    # Clean the base file
    df = clean_base_file(df)
    # Prepare current week's data
    current_week_df = prepare_current_week_data(current_week_data)
    # Append current week's data to the base file DataFrame
    updated_df = pd.concat([df, current_week_df], ignore_index=True)
    # Save the updated DataFrame to the base file
    updated_df.to_csv(base_file_path, index=False)

def create_backup(base_file_path):
    """
    Creates a backup of the existing base file by appending the current date to the filename.
    
    Args:
    - base_file_path (str): The path to the base file.
    
    Returns:
    - None
    """
    # Get the directory and filename from the base file path
    dir_name, file_name = os.path.split(base_file_path)
    # Get the file name without the extension and the file extension
    file_base, file_ext = os.path.splitext(file_name)

    # Create a timestamp in the format YYYYMMDD
    timestamp = datetime.now().strftime('%m-%d-%H-%M-%S')

    # Construct the backup file name with the date appended
    backup_file_name = f"{file_base}_{timestamp}{file_ext}"

    # Construct the full path for the backup file
    backup_file_path = os.path.join(dir_name, backup_file_name)

    # Create a copy of the base file with the new name
    shutil.copy2(base_file_path, backup_file_path)

# Function to read and normalize the current week's attendance data
def input_attendance_data(new_report, base_file, column_mapping):
    """
    Reads the current week's attendance data from the provided CSV file,
    converts it into a dictionary, and applies column mappings to standardize column names.

    Args:
    - new_report (str): The path to the CSV file containing the current week's attendance data.
    - base_file (str): The path to the base CSV file containing historical attendance data.
    - column_mapping (dict): A dictionary mapping old column names to new standardized column names.

    Returns:
    - tuple: Three dictionaries with normalized attendance data for the current week, one week back, and two weeks back.
    """

    #create individual dicts for each week
    current_week_data = df_to_dict(read_csv(new_report, column_mapping))
    current_week_data = consolidate_attendance(current_week_data)  # Consolidate attendance

    if base_file_exists(base_file): 
        one_week_prior_df, two_weeks_prior_df = read_previous_weeks(base_file, column_mapping)
        one_week_prior_data = df_to_dict(one_week_prior_df)
        two_weeks_prior_data = df_to_dict(two_weeks_prior_df)
    else:
        one_week_prior_data = []
        two_weeks_prior_data = []

    return current_week_data, one_week_prior_data, two_weeks_prior_data
    
# Function to read and normalize previous weeks' data from the base file
def read_previous_weeks(base_file_path, column_mapping):
    """
    Reads the base file containing historical attendance data, separates the data into two DataFrames:
    one for the data from one week back (week -1) and another for the data from two weeks back (week -2).

    Args:
    - base_file_path (str): The path to the base CSV file containing historical attendance data.
    - column_mapping (dict): A dictionary mapping old column names to new standardized column names.

    Returns:
    - tuple: Two DataFrames with data from one week back and two weeks back.
    """

    df = read_csv(base_file_path, column_mapping)
    one_week_prior_df = df[df['weekly_value'] == -1]
    two_weeks_prior_df = df[df['weekly_value'] == -2]
    return one_week_prior_df, two_weeks_prior_df

# Function to process an attendance dictionary and cosolidate attendance records for each student 
# into a single record of attednance across any buildings they attended for the year
def consolidate_attendance(attendance_data):
    """
    Consolidates attendance records for each student across multiple buildings into a single record
    representing their attendance for the year.
    
    Args:
    - attendance_data (dict): A dictionary containing attendance data for the current week.
    
    Returns:
    - dict: A dictionary with consolidated attendance data for each student.
    """
    consolidated_data = {}
    for record in attendance_data:
        student_id = record['student_number']
        if student_id not in consolidated_data:
            consolidated_data[student_id] = {
                'student_number': student_id,
                'name': record['name'],
                'grade': record['grade'],
                'hrs_attended': 0,
                'hrs_absent': 0,
                'hrs_possible': 0,
                'ind_att_percent': 0
            }
        consolidated_data[student_id]['hrs_attended'] += record['hrs_attended']
        consolidated_data[student_id]['hrs_absent'] += record['hrs_absent']
        consolidated_data[student_id]['hrs_possible'] += record['hrs_possible']
        
        # Calculate attendance percentage
        total_attended = consolidated_data[student_id]['hrs_attended']
        total_possible = consolidated_data[student_id]['hrs_possible']
        if total_possible > 0:
            attendance_percentage = (total_attended / total_possible) * 100
            consolidated_data[student_id]['ind_att_percent'] = round(attendance_percentage, 2)
        else:
            # Reset ind_att_percent to 0 if hrs_possible is 0
            consolidated_data[student_id]['ind_att_percent'] = 0

        
        consolidated_data[student_id]['ind_att_percent'] = round(attendance_percentage, 2)  # Round to two decimal places

    # Exclude records where hrs_possible is 0
    consolidated_list = [data for data in consolidated_data.values() if data['hrs_possible'] > 0]

    #consolidated_list = list(consolidated_data.values())
    return consolidated_list

def prime_results(current_week_data):
    """
    Primes the results dictionary with the current week's attendance data.
    
    Args:
    - current_week_data (dict): The dictionary containing the current week's attendance data.
    
    Returns:
    - dict: A dictionary with the current week's attendance data.
    """
    
    results = {}
    for i, student in enumerate(current_week_data):

        if 'student_number' in student and 'ind_att_percent' in student:
            student_id = student['student_number']
            current_att_percent = student['ind_att_percent']
            below_90_1_week = current_att_percent < 90
            results[student_id] = {
                'student_number': student_id,
                'name': student['name'],
                'grade': student['grade'],
                'current_week_att_percent': current_att_percent,
                'below_90_1_week': below_90_1_week
            }
            

        else:
            print(f"Invalid student data: {student}")
    
    return results


def compare_one_week_back(current_week_data, one_week_back_data, results):
    """
    Compares the current week's attendance data against the data from one week back,
    identifies changes in attendance (improvement, decline, no change), and stores these comparisons.

    Args:
    - current_week_data (list): The list of dictionaries containing the current week's attendance data.
    - one_week_back_data (list): The list of dictionaries containing the attendance data from one week back.
    - results (dict): The results dictionary to be updated with one-week comparison data.

    Returns:
    - dict: An updated dictionary containing the results of the comparison.
    """
    if not one_week_back_data:
        return results
    
    for student in current_week_data:
        student_id = student['student_number']
        current_att_percent = student['ind_att_percent']
        
        one_week_student = next((s for s in one_week_back_data if s['student_number'] == student_id), None)

        if one_week_student:
            one_week_att_percent = one_week_student.get('ind_att_percent', None)
       
        # Check if the student is below 90% for two consecutive weeks
        below_90_2_weeks = current_att_percent < 90 and one_week_att_percent is not None and one_week_att_percent < 90
           
        results[student_id].update({
            'one_week_back_percent': one_week_att_percent,
            'below_90_2_weeks': below_90_2_weeks,
            'trend_1_week': (
               'Up' if one_week_att_percent is not None and current_att_percent > one_week_att_percent
                else 'Down' if one_week_att_percent is not None and current_att_percent < one_week_att_percent
                else 'No Change' if one_week_att_percent is not None else 'N/A'
            )
        })
    
    return results

def compare_two_weeks_back(current_week_data, two_weeks_back_data, results):
    """
    Compares the current week's attendance data against the data from two weeks back,
    identifies changes in attendance (improvement, decline, no change), and stores these comparisons.

    Args:
    - current_week_data (list): The list of dictionaries containing the current week's attendance data.
    - two_weeks_back_data (list): The list of dictionaries containing the attendance data from two weeks back.
    - results (dict): The results dictionary from compare_one_week_back to be updated with two weeks data.

    Returns:
    - dict: An updated dictionary containing the results of the comparison with two weeks data.
    """
    if not two_weeks_back_data:
        return results
    for student in current_week_data:
        student_id = student['student_number']
        current_att_percent = student['ind_att_percent']
        
        two_weeks_student = next((s for s in two_weeks_back_data if s['student_number'] == student_id), None)
        if two_weeks_student:
            two_weeks_att_percent = two_weeks_student.get('ind_att_percent', None)
            below_90_3_weeks = (current_att_percent < 90 and
                                results[student_id]['one_week_back_percent'] < 90 and
                                two_weeks_att_percent < 90)
            
            results[student_id].update({
                'two_weeks_back_percent': two_weeks_att_percent,
                'below_90_3_weeks': below_90_3_weeks,
                'trend_2_weeks': (
                    'Up' if current_att_percent > two_weeks_att_percent
                    else 'Down' if current_att_percent < two_weeks_att_percent
                    else 'No Change' if two_weeks_att_percent is not None else 'N/A'
                )
            })
    return results

def flag_attendance_issues(current_week, one_week_back, two_weeks_back):
    """
    Flags attendance issues based on the current week's attendance data and comparisons with previous weeks.
    Flags include trending up/down, and whether the student has been below 90% for 1, 2, or 3 weeks.

    Args:
    - current_week (list): The list of dictionaries containing the current week's attendance data.
    - one_week_back (list): The list of dictionaries containing the attendance data from one week back.
    - two_weeks_back (list): The list of dictionaries containing the attendance data from two weeks back.

    Returns:
    - dict: A dictionary containing the flagged attendance issues.
    """
    results = prime_results(current_week)
    results = compare_one_week_back(current_week, one_week_back, results)
    results = compare_two_weeks_back(current_week, two_weeks_back, results)
    return results

# Function to load and normalize additional data
def load_additional_data(ps_data_path, ps_data_mapping, probation_data_path, probation_data_mapping,
                                    med_data_path, medp_data_path, med_data_mapping, medp_data_mapping):
    """
    Reads and normalizes additional data from the provided CSV file, converting it into a dictionary and applying column mappings.
    
    Args:
    - file_path (str): The path to the CSV file containing additional data.
    - column_mapping (dict): A dictionary mapping old column names to new standardized column names.
    
    Returns:
    - dict: A dictionary with normalized additional data.
    """
   
    ps_data = df_to_dict(read_csv(ps_data_path, ps_data_mapping))
    print(f"🔍 Loaded {len(ps_data)} students from ps_data.csv")
    pa_data = df_to_dict(read_csv(probation_data_path, probation_data_mapping))

    # Convert all student_number to floats in pa_data
    for record in pa_data:
        if 'student_number' in record:
            try:
                record['student_number'] = float(record['student_number'])
            except ValueError:
                record['student_number'] = None  # Handle conversion errors, if any

    #***************************new***************************
    # Load MED and MEDP data
    med_data = df_to_dict(read_csv(med_data_path, med_data_mapping))
    medp_data = df_to_dict(read_csv(medp_data_path, medp_data_mapping))
    #***************************new***************************

    return ps_data, pa_data, med_data, medp_data

# Function to process additional data and integrate with attendance data
def process_additional_data(results_dict, additional_data):
    """
    Processes the additional data sets and integrates them with the results dictionary,
    adding relevant information based on the comparisons and other data processing.
    
    Args:
    - results_dict (dict): The dictionary containing the results of the attendance data comparisons.
    - additional_data (tuple): A tuple containing dictionaries of additional data to be integrated.
    
    Returns:
    - dict: The updated results dictionary with additional data integrated.
    """
    ps_data, probation_data, med_data, medp_data = additional_data[:4]  # Unpack med_data and medp_data

   

    # Update results_dict with data from PowerSchool data
    for ps_student in ps_data:
        
        student_id = ps_student['student_number']
        if student_id in results_dict:

            # Parse DOB and calculate age
            
            dob_str = ps_student['dob']
            if dob_str:
                try:
                    # Parse the DOB string to a datetime object
                    dob = datetime.strptime(dob_str, "%Y-%m-%d %H:%M:%S.%f")
                    # Format DOB to just the date without time
                    dob_formatted = dob.strftime("%Y-%m-%d")
                    # Calculate age
                    today = datetime.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                except ValueError:
                    dob_formatted = "Invalid Date"
                    age = "Unknown"
            else:
                dob_formatted = "Unknown"
                age = "Unknown"
            
            # Create full_name and only append middle name if it exists and is not nan or None
            middle_name = ps_student['middle_name']
            if middle_name and isinstance(middle_name, str) and not (middle_name == '' or middle_name.lower() == 'nan'):
                full_name = f"{ps_student['last_name']}, {ps_student['first_name']} {middle_name}".strip()
            else:
                full_name = f"{ps_student['last_name']}, {ps_student['first_name']}".strip()
                        
            results_dict[student_id].update({
                'dob': dob_formatted,
                'age': age,
                'attending_school': ps_student['attending_school'],
                'school_of_residence': ps_student['school_of_residence'],
                'home_room': ps_student['home_room'],
                'street': ps_student['street'],
                'city': ps_student['city'],
                'state': ps_student['state'],
                'zip': ps_student['zip'],
                'current_rel_type_code_set_id': ps_student['current_rel_type_code_set_id'],
                'is_custodial': ps_student['is_custodial'],
                'lives_with': ps_student['lives_with'],
                'receives_mail': ps_student['receives_mail'],
                'full_name': full_name,
                'email_address': ps_student['email_address'],
                'phone_number': ps_student['phone_number'],
                'phone_number_ext': ps_student['phone_number_ext'],
                'is_sms': ps_student['is_sms'],
                'is_preferred': ps_student['is_preferred'],
                'Team': ps_student.get('Team', 'N/A'),
            })
           
    
    for pa_student in probation_data:
        student_id = pa_student['student_number']
        if student_id in results_dict:
            results_dict[student_id].update({
                'current_status': pa_student.get('current_status', 'N/A'),
                'end_date': pa_student.get('end_date', 'N/A'),                
                'pa_letter_1': pa_student.get('pa_letter_1', 'N/A'),
                'pa_letter_2': pa_student.get('pa_letter_2', 'N/A'),  # New field for PA Letter 2
                'last_updated': pa_student.get('last_updated', 'N/A'), # New field for Last Up Dated
                'notes': pa_student.get('notes', 'No notes available')
            })

    #***************************new***************************
    # Initialize and count MED and MEDP occurrences for each student in the results_dict
    med_counts = {}
    medp_counts = {}

    # Count MED entries
    for record in med_data:
        student_id = record['student_number']
        if student_id not in med_counts:
            med_counts[student_id] = 0
        med_counts[student_id] += 1

    # Count MEDP entries
    for record in medp_data:
        student_id = record['student_number']
        if student_id not in medp_counts:
            medp_counts[student_id] = 0
        medp_counts[student_id] += 1

    # Add counts and absence percentage to results_dict
    for student_id, data in results_dict.items():
        med_full_days = med_counts.get(student_id, 0)
        med_partial_days = medp_counts.get(student_id, 0)

        # Assign counts to the results
        data['Med Full days'] = med_full_days
        data['Med Partial days'] = med_partial_days

        # Calculate the absence percentage equivalent for MED days
        med_absence_percent = calculate_med_absence_percentage(med_full_days, med_partial_days)
        data['Med Absence Percent'] = med_absence_percent

        # Calculate the best-case attendance by adding Med Absence Percent to current attendance
        current_attendance = data.get('current_week_att_percent', 0)
        data['Best Case Attendance Percent'] = min(current_attendance + med_absence_percent, 100.0)  # Cap at 100%
    
    #***************************new***************************
               

    return results_dict

def calculate_med_absence_percentage(med_full_days, med_partial_days):
    """
    Calculates the absence percentage contributed by MED days, treating both full and partial days as full days.
    """
    if TOTAL_SCHOOL_DAYS == 0:
        return 0.0  # Avoid division by zero if no school days have passed

    total_med_days = med_full_days + med_partial_days
    absence_percentage = (total_med_days / TOTAL_SCHOOL_DAYS) * 100

    return round(absence_percentage, 2)  # Round to one decimal place for whole-number representation


# Function to create output folders for each building
def create_building_folders(base_output_path, buildings):
    """
    Creates separate folders for each building in the specified base output path.
    
    Args:
    - base_output_path (str): The path where the building folders will be created.
    - buildings (list): A list of building names.
    
    Returns:
    - None
    """
    if not os.path.exists(base_output_path):
        os.makedirs(base_output_path)
    for building in buildings:
        building_path = os.path.join(base_output_path, building)
        if not os.path.exists(building_path):
            os.makedirs(building_path)

def generate_building_csvs(results_dict, building_group_mapping, base_output_path, column_order):
    """
    Generates CSV files for each building group from the final results dictionary
    and saves them in the corresponding building folders.
    
    Args:
    - results_dict (dict): The dictionary containing all processed and merged data.
    - building_group_mapping (dict): A dictionary mapping building groups to lists of school names.
    - base_output_path (str): The base directory where the building folders and CSV files will be saved.
    
    Returns:
    - None
    """

    output_path = get_output_dir(base_output_path, TESTING_MODE)
        
    uncategorized_students = []  # List to store students that don't fit into any building group

    for group_name, schools in building_group_mapping.items():
        filtered_students = [
            student for student in results_dict.values() 
            if student['school_of_residence'] in schools
        ]
        
        if not filtered_students:
            continue  # Skip if no students are found for this group

        # Apply generic customization function
        #filtered_students = apply_customizations(group_name, filtered_students)

        building_path = os.path.join(output_path, group_name)
        os.makedirs(building_path, exist_ok=True)
        
        df = pd.DataFrame(filtered_students)

        # Reorder the columns based on the specified order
        df = reorder_columns(df, column_order)
        
        df.to_csv(os.path.join(building_path, f"{group_name}_attendance.csv"), index=False)

        # Optional: Generate additional filtered CSVs for attendance categories
        generate_additional_building_csvs(filtered_students, building_path, group_name, column_order)

         # Combine all CSVs for this group into one Excel workbook
        combine_csvs_into_workbook(building_path, workbook_name=f"{group_name}_combined_workbook.xlsx", group_name=group_name)


    # Now handle the uncategorized students
    for student in results_dict.values():
        # Check if the school_of_residence is not in any of the defined groups
        if not any(student['school_of_residence'] in schools for schools in building_group_mapping.values()):
            uncategorized_students.append(student)
    
    # If there are any uncategorized students, create a separate CSV for them
    if uncategorized_students:
        uncategorized_path = os.path.join(output_path, 'Uncategorized')
        os.makedirs(uncategorized_path, exist_ok=True)
        
        df_uncategorized = pd.DataFrame(uncategorized_students)
        # Reorder the columns for uncategorized students
        df_uncategorized = reorder_columns(df_uncategorized, column_order)

        df_uncategorized.to_csv(os.path.join(uncategorized_path, "uncategorized_attendance.csv"), index=False)

def generate_additional_building_csvs(filtered_students, building_path, group_name, column_order):
    """
    Generates additional CSV files for different attendance categories.
    
    Args:
    - filtered_students (list): The list of student dictionaries to be filtered.
    - building_path (str): The directory where the CSVs will be saved.
    
    Returns:
    - None
    """
    df = pd.DataFrame(filtered_students)
    subsets = {
        '90_to_100': df[(df['current_week_att_percent'] >= 90) & (df['current_week_att_percent'] <= 100)],
        '80_to_90': df[(df['current_week_att_percent'] >= 80) & (df['current_week_att_percent'] < 90)],
        '50_to_80': df[(df['current_week_att_percent'] >= 50) & (df['current_week_att_percent'] < 80)],
        '0_to_50': df[(df['current_week_att_percent'] >= 0) & (df['current_week_att_percent'] < 50)],
        # Custom weighted points subsets
        'below_85_zero_weighted_points': df[df['current_week_att_percent'] < 85],  # Below 85, does not include 85
        '85_to_87.5_quarter_weighted_points': df[(df['current_week_att_percent'] >= 85) & (df['current_week_att_percent'] < 87.5)],  # 85 to below 87.5
        '87.5_to_90_half_weighted_points': df[(df['current_week_att_percent'] >= 87.5) & (df['current_week_att_percent'] < 90)],  # 87.5 to below 90
        '90_and_above_full_weighted_point': df[df['current_week_att_percent'] >= 90],  # 90 and above
        # Apply the custom filtering logic and name the subset
        'Qualify_For_Letters': filter_subset_by_conditions(df),
        '0_to_80': df[(df['current_week_att_percent'] > 0) & (df['current_week_att_percent'] < 80)]
    }
    
    for subset_name, subset_students in subsets.items():
        if not subset_students.empty:
            csv_filename = os.path.join(building_path, f"{subset_name}_{group_name}_attendance.csv")
            df = pd.DataFrame(subset_students)
            # Reorder the columns
            df = reorder_columns(df, column_order)
            df.to_csv(csv_filename, index=False)

def combine_csvs_into_workbook(output_dir, workbook_name="combined_workbook.xlsx", group_name=None):
    """
    Combines all CSV files in the output directory into a single Excel workbook in a specific order.
    
    Args:
    - output_dir (str): The directory where the CSV files are located.
    - workbook_name (str): The name of the output Excel workbook.
    - group_name (str): The name of the group, which will help identify the master file.
    
    Returns:
    - None
    """
    # Suppress warnings for sheet names longer than 31 characters
    warnings.filterwarnings("ignore", category=UserWarning, message=".*title.*31 characters*")

    # Define the desired order for the subsets
    subset_order = [
        "90_to_100",
        "80_to_90",
        "50_to_80",
        "0_to_50",
        "below_85_zero_weighted_points",
        "85_to_87.5_quarter_weighted_points",
        "87.5_to_90_half_weighted_points",
        "90_and_above_full_weighted_point",
        "Qualify_For_Letters",
        "0_to_80"
    ]
    
    # Sort the CSV files
    csv_files = os.listdir(output_dir)
    
    # Prioritize the group_name file (master) first, followed by subsets in the specific order
    sorted_csv_files = sorted(
        csv_files,
        key=lambda x: (
            0 if x.startswith(group_name) else  # Master file goes first
            next((i + 1 for i, subset in enumerate(subset_order) if subset in x), len(subset_order) + 1)  # Subset order
        )
    )

    workbook_path = os.path.join(output_dir, workbook_name)
    #print(f"\nStarting workbook: {workbook_path}")
    
    with pd.ExcelWriter(workbook_path, engine='openpyxl') as writer:
        # Loop through sorted files in the directory
        for file_name in sorted_csv_files:
            if file_name.endswith('.csv'):
                file_path = os.path.join(output_dir, file_name)
                #print(f"Processing CSV file: {file_path} into workbook: {workbook_name}")
                
                # Read each CSV file
                df = pd.read_csv(file_path)
                
                # Use the file name (without extension) as the sheet name
                sheet_name = os.path.splitext(file_name)[0]
                #print(f"Writing sheet: {sheet_name[:31]} into workbook: {workbook_name}")
                
                # Write each DataFrame to a different sheet
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

                # Delete the CSV file after adding it to the workbook
                os.remove(file_path)
                #print(f"Deleted CSV file: {file_path}")
    
    print(f"All CSV files have been combined into {workbook_name}\n")

def filter_subset_by_conditions(df):
    """
    Filters the DataFrame based on a series of conditions described in the Excel filter instructions.
    
    Args:
    - df (DataFrame): The DataFrame to be filtered.
    
    Returns:
    - DataFrame: A DataFrame filtered based on the specified conditions.
    """

    # Column J (Below 90 - 3 Weeks): Select TRUE only and apply a condition where the value is below 90
    df = df[(df['below_90_3_weeks'] == True) & (df['current_week_att_percent'] < 90)]
    
    # Column K (Trend - 2 Weeks): Select "Down" from the options
    df = df[df['trend_2_weeks'] == 'Down']
    
    # Column H (Trend - 1 Week): Select "Down" from the options
    df = df[df['trend_1_week'] == 'Down']
    
    # Column G (Below 90 - 2 Weeks): Select TRUE only
    df = df[df['below_90_2_weeks'] == True]
    
    # Column E (Below 90 - 1 Week): Select TRUE only
    df = df[df['below_90_1_week'] == True]
    
    # Column D (Current Week Attendance Percent): Select >= 80
    df = df[df['current_week_att_percent'] >= 70]

    return df

def map_school_codes(results_dict, school_dict):
    """
    Maps numeric school codes to school names for 'attending_school' and 'school_of_residence'
    in the results dictionary. Displays the unknown school code if it's not mapped.

    Args:
    - results_dict (dict): The dictionary containing the attendance data with numeric school codes.
    - school_dict (dict): The dictionary mapping school codes to school names.

    Returns:
    - dict: The updated results dictionary with school names instead of numeric codes.
    """
    for student_id, student_data in results_dict.items():
        # Map attending_school code to school name
        attending_code = student_data.get('attending_school')
        if attending_code in school_dict:
            student_data['attending_school'] = school_dict[attending_code]
        else:
            student_data['attending_school'] = f"Unknown School (Code: {attending_code})"

        # Map school_of_residence code to school name
        residence_code = student_data.get('school_of_residence')
        if residence_code in school_dict:
            student_data['school_of_residence'] = school_dict[residence_code]
        else:
            student_data['school_of_residence'] = f"Unknown School (Code: {residence_code})"

    return results_dict



# Function to generate the final report and save it to a CSV file
def generate_final_report(results_dict, output_file_path, column_order):
    """
    Converts the final results dictionary into a DataFrame, performs any final data cleaning and formatting,
    and saves it to a CSV file.
    
    Args:
    - results_dict (dict): The dictionary containing all processed and merged data.
    - output_file_path (str): The path where the final output CSV file will be saved.
    
    Returns:
    - None
    """
    output_dir = get_output_dir(os.path.dirname(output_file_path), TESTING_MODE)
    output_file = os.path.join(output_dir, os.path.basename(output_file_path))
    
    results_list = list(results_dict.values())
    df = pd.DataFrame(results_list)

    # Reorder the columns 
    df = reorder_columns(df, column_order)


    df.to_csv(output_file, index=False)

def filter_unknown_schools(results_dict):
    """
    Filters out records from the results dictionary where the 'school_of_residence'
    is set to 'Unknown School (Code: None)'.
    
    Args:
    - results_dict (dict): The dictionary containing student records to be filtered.
    
    Returns:
    - dict: The filtered results dictionary with unwanted records removed.
    """
    # Create a new dictionary excluding records with 'school_of_residence' as 'Unknown School (Code: None)'
    filtered_results = {
        student_id: data
        for student_id, data in results_dict.items()
        if data.get('school_of_residence') != 'Unknown School (Code: None)'
    }
    
    return filtered_results

def apply_customizations(building_name, students):
    """
    Applies any customizations needed for a specific building before saving to CSV.
    
    Args:
    - building_name (str): The name of the building group.
    - students (dict): Dictionary of student dictionaries for that building group.
    
    Returns:
    - dict: Modified dictionary of student dictionaries with customizations applied.
    """
    # Check if there is a customization function for the building
    if 'Middle School 4' in building_name:
        students = customize_Middle_School_4_data(students)
    # Additional building customizations can be added here

    return students

def customize_Middle School_4_data(students):
    """
    Customizes the data for the Middle School 4 building by adding a 'Team' column.
    
    Args:
    - students (dict): Dictionary of student dictionaries.
    
    Returns:
    - dict: Modified dictionary of student dictionaries with the 'Team' column added.
    """
    for student_id, student in students.items():
        student['Team'] = student.get('Team', '')  # Ensure 'Team' column is added or kept if exists
    return students

def get_output_dir(base_output_path, is_testing):
    """
    Returns the appropriate output directory based on the testing mode.
    
    Args:
    - base_output_path (str): The base output path for production.
    - is_testing (bool): A flag indicating if the script is running in testing mode.
    
    Returns:
    - str: The appropriate output directory.
    """
    if is_testing:
        test_output_dir = os.path.join(base_output_path, '#test_output')
        if not os.path.exists(test_output_dir):
            os.makedirs(test_output_dir)
        return test_output_dir
    return base_output_path

def reorder_columns(df, column_order):
    """
    Reorders the columns of a DataFrame based on the specified column order.

    Args:
    - df (DataFrame): The DataFrame to reorder.
    - column_order (list): A list of column names in the desired order.

    Returns:
    - DataFrame: The DataFrame with columns reordered.
    """
    # Filter column order list to include only columns that are present in the DataFrame
    ordered_columns = [col for col in column_order if col in df.columns]
    return df[ordered_columns]

def generate_alt_hr_report(results_dict, schools_to_include, base_output_path, column_order):
    """
    Generates a report for students attending specific schools (alt and HR) and saves it in a designated folder.

    Args:
    - results_dict (dict): The dictionary containing all processed and merged data.
    - schools_to_include (list): A list of schools to include in the report.
    - base_output_path (str): The base output path for production.
    - column_order (list): The desired column order for the report.

    Returns:
    - None
    """
    global TESTING_MODE  # Use the global TESTING_MODE variable

    # Determine the output directory based on testing mode
    output_dir = get_output_dir(base_output_path, TESTING_MODE)

    # Define the subdirectory path for alt and HR
    sub_dir = os.path.join(output_dir, "alt and HR")
    os.makedirs(sub_dir, exist_ok=True)

    # Filter results based on the list of schools
    filtered_results = [
        student for student in results_dict.values()
        if student.get('attending_school') in schools_to_include
    ]
    
    if not filtered_results:
        print(f"No students found for the selected schools: {schools_to_include}")
        return
    
    # Convert the filtered results to a DataFrame
    df = pd.DataFrame(filtered_results)
    df = reorder_columns(df, column_order)
    
    # Create the output file path
    output_file = os.path.join(sub_dir, "alt_and_HR_report.csv")
    
    # Save the filtered data to CSV
    df.to_csv(output_file, index=False)
    print(f"alt and HR report saved to {output_file}")


def main():
    # Define file paths and column mappings
    current_week_file = 'YTD Student Attendance Extract.csv'
    base_file = 'base_file.csv'
    ps_data_file = 'PS_data.csv'
    probation_data_file = 'PA_data.csv'
    med_data_file = 'med.csv'  #***************************new***************************
    medp_data_file = 'medp.csv'  #***************************new***************************
    output_dir = 'output'
    output_file = os.path.join(output_dir, 'final_report.csv')
    
    #***************************new***************************
    # Mapping dictionaries for med.csv and medp.csv
    med_data_mapping = {
        'StudNum': 'student_number',
        'Att Code': 'att_code'
    }
    medp_data_mapping = {
        'StudNum': 'student_number',
        'Att Code': 'att_code'
    }
    #***************************new***************************

    attendance_mapping = {
        'Count': 'count',
        'Reporting School': 'reporting_school',
        'Attending School': 'attending_school',
        'MOSIS ID': 'mosis_id',
        'Student Number': 'student_number',
        'Name': 'name',
        'Grade': 'grade',
        'Hrs Attended': 'hrs_attended',
        'Hrs Absent': 'hrs_absent',
        'Hrs Possible': 'hrs_possible',
        'Ind Att %': 'ind_att_percent',
        'Segment': 'segment',
        'Tot Hrs for Period': 'total_hrs_period',
        'Att Pts': 'att_pts',
        'Adj Prop Wt': 'adj_prop_wt'
    }
    ps_data_mapping = {
        'StudentNumber': 'student_number',
        'DOB': 'dob',
        'AttendingSchool': 'attending_school',
        'SchoolofResidence': 'school_of_residence',
        'Home_Room': 'home_room',
        'Street': 'street',
        'City': 'city',
        'State': 'state',
        'Zip': 'zip',
        'CurrRelTypeCodeSetID': 'current_rel_type_code_set_id',
        'IsCustodial': 'is_custodial',
        'LivesWith': 'lives_with',
        'ReceivesMail': 'receives_mail',
        'FirstName': 'first_name',
        'MiddleName': 'middle_name',
        'LastName': 'last_name',
        'EmailAddress': 'email_address',
        'PhoneNumber': 'phone_number',
        'PhoneNumberExt': 'phone_number_ext',
        'IsSMS': 'is_sms',
        'IsPreferred': 'is_preferred'
    }
    
    # Mapping for the consolidated PA data CSV
    pa_data_mapping = {
        'Student ID #': 'student_number',          # Updated to match the new header for student number
        'Current Status': 'current_status',        # Existing field in the script
        'END DATE': 'end_date',                    # Existing field in the script
        'Notes:': 'notes',                         # Existing field in the script
        'PA Letter 1': 'pa_letter_1',              # Existing field in the script
        'PA Letter 2': 'pa_letter_2',              # Newly added field
        'Last Up Dated': 'last_updated'            # Newly added field
    }
    
    # Create a dictionary for school codes and corresponding names
    school_dict = {
        #high schools
        1: 'High School 1',
        2: 'High School 2',
        3: 'High School 3',
        #middle schools
        4: 'Middle School 1',
        5: 'Middle School 2',
        6: 'Middle School 3',
        7: 'Middle School 4',
        #elementary schools
        8: 'Elementary School 1',
        9: 'Elementary School 2',
        10: 'Elementary School 3',
        11: 'Elementary School 4',
        12: 'Elementary School 5',
        13: 'Elementary School 6',
        14: 'Elementary School 7',
        15: 'Elementary School 8',
        16: 'Elementary School 9',
        17: 'Elementary School 10',
        18: 'Elementary School 10',
        19: 'Elementary School 11',
        20: 'Elementary School 12',
        21: 'Elementary School 13',
        22: 'alt HS',
        23: 'alt Elem',
        24: 'TechSchool',
        25: 'private secondary',
        26: 'alternativeprog',
        27: 'alternativeprog',
        28: 'alternativeprog',
        29: 'alt MS',
        30: 'Out of Dist Elem',
        31: 'ELC',
        32: 'ELC'
    }
    
    # Define the building group mapping using school names
    
    building_group_mapping = {
        'team 1': ['High School 1'],
        'team 3': ['High School 2'],
        'team 4': ['Middle School 3'],
        'team 5': ['High School 3'],
        'team 6': ['Middle School 4', 'Elementary School 1'],
        'team 7': ['Middle School 1'],
        'team 8': ['Elementary School 9'],
        'team 9': ['Elementary School 6', 'Elementary School 10'],
        'team 10': ['Elementary School 7', 'Elementary School 8'],
        'team 11': ['Elementary School 12', 'Elementary School 3'],
        'team 12': ['Elementary School 13', 'Middle School 2', 'Elementary School 2', 'Elementary School 5', 'Elementary School 4', 'Elementary School 11'],

        'Elementary School 13': ['Elementary School 13'],
        'Middle School 2': ['Middle School 2'],
        'Elementary School 2': ['Elementary School 2'],
        'Elementary School 5': ['Elementary School 5'],
        'Elementary School 4': ['Elementary School 4'],
        'Elementary School 11': ['Elementary School 11'],
        'Elementary School 6': ['Elementary School 6'],

        'ELC - Not used': ['ELC'],
        
        'Middle School 3': ['Middle School 3'],
        'Elementary School 1': ['Elementary School 1'],
        'Middle School 4': ['Middle School 4'],
        'High School 1': ['High School 1'],
        'Elementary School 8': ['Elementary School 8'],
        
        'District': ['High School 1', 'High School 2', 'High School 3', 'Middle School 1', 'Middle School 2', 'Middle School 3',
                     'Middle School 4', 'Elementary School 1', 'Elementary School 5', 'Elementary School 6', 'Elementary School 2', 'Elementary School 3',
                     'Elementary School 4', 'Elementary School 8', 'Elementary School 9', 'ELC', 'Elementary School 10', 'Elementary School 11', 'Elementary School 12',
                     'Elementary School 13', 'alt HS', 'alt Elem', 'TechSchool', 'private secondary', 'alternativeprog',
                     'alt MS', 'ELC', 'Elementary School 7']
    }

    DESIRED_COLUMN_ORDER = [
    'student_number',
    'name',
    'grade',
    'current_week_att_percent',
    'Med Full days',
    'Med Partial days',
    'Med Absence Percent',
    'Best Case Attendance Percent',
    'below_90_1_week',
    'one_week_back_percent',
    'below_90_2_weeks',
    'trend_1_week',
    'two_weeks_back_percent',
    'below_90_3_weeks',
    'trend_2_weeks',
    'attendance_category',
    'dob',
    'age',
    'attending_school',
    'school_of_residence',
    'home_room',
    'Team',
    'current_status',
    'end_date',
    'pa_letter_1',
    'pa_letter_2',
    'last_updated',
    'notes',
    'street',
    'city',
    'state',
    'zip',
    'current_rel_type_code_set_id',
    'is_custodial',
    'lives_with',
    'receives_mail',
    'full_name',
    'email_address',
    'phone_number',
    'phone_number_ext',
    'is_sms',
    'is_preferred'
]

    

    # Step 1: Read and normalize current week data
    current_week_data, one_week_back_data, two_weeks_back_data = input_attendance_data(current_week_file, base_file, attendance_mapping)
    print(f"✅ Loaded students from current week file: {len(current_week_data)}")


    # Step 2: Prime the results dictionary
    results = prime_results(current_week_data)

    # Step 3: Compare one week back
    results = compare_one_week_back(current_week_data, one_week_back_data, results)
    print(f"✅ Students after one-week comparison: {len(results)}")


    # Step 4: Compare two weeks back
    results = compare_two_weeks_back(current_week_data, two_weeks_back_data, results)
    print(f"✅ Students after two-week comparison: {len(results)}")


    # Step 5: Load and process additional data
    #***************************changed***************************
    additional_data = load_additional_data(ps_data_file, ps_data_mapping, probation_data_file, pa_data_mapping,
                                            med_data_file, medp_data_file, med_data_mapping, medp_data_mapping)  
    results = process_additional_data(results, additional_data)
    print(f"✅ Students after processing additional data (ps_data, med data and PA data: {len(results)}")

    results = map_school_codes(results, school_dict)

    # Remove records with 'Unknown School (Code: None)' as school_of_residence
    print(f"✅ Students before filter_unknown_schools: {len(results)}")

    # Get all unique values of school_of_residence before filtering
    unique_schools = set(student.get('school_of_residence') for student in results.values())
    print(f"🧐 Unique school_of_residence values before filtering: {unique_schools}")

    results = filter_unknown_schools(results)
    print(f"✅ Students after filter_unknown_schools: {len(results)}")


    # Step 6: Add the attendance category
    results = add_attendance_category(results)

    
    if not TESTING_MODE:
        # Step 6: Update the base file with the current week data
        update_base_file(current_week_data, base_file, attendance_mapping)
        
        print(f'Results have been written to {output_file}')
    # Clear old CSV files in all building directories before generating new ones
    clear_old_csvs_in_all_buildings(output_dir, building_group_mapping)

    generate_building_csvs(results, building_group_mapping, output_dir, DESIRED_COLUMN_ORDER)
    # Step 7: Generate the final report using the function
    generate_final_report(results, output_file, DESIRED_COLUMN_ORDER)
    
    # Step: Generate the alt and HR report
    schools_to_include = ["alternativeprog", "alt Elem", "alt HS", "alt MS"]
    generate_alt_hr_report(results, schools_to_include, output_dir, DESIRED_COLUMN_ORDER)


if __name__ == '__main__':
    main()
