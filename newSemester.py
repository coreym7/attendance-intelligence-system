import pandas as pd
import os
from datetime import datetime

# Global Configuration
SEMESTER_START_DATE = "1/1/1999"
TOTAL_SEMESTER_DAYS = 1 #as of (Date)

# Column mappings
attendance_mapping = {
    "Count": "count",
    "Reporting School": "reporting_school",
    "Attending School": "attending_school",
    "MOSIS ID": "mosis_id",
    "Student Number": "student_number",
    "Name": "name",
    "Grade": "grade",
    "Hrs Attended": "hrs_attended",
    "Hrs Absent": "hrs_absent",
    "Hrs Possible": "hrs_possible",
}

med_mapping = {
    "StudNum": "student_number",
    "Attendance Date": "date",
}

medp_mapping = {
    "StudNum": "student_number",
    "Attendance Date": "date",
}

# Utility Functions
def read_csv_to_dict(file_path, column_mapping):
    """
    Reads a CSV file into a DataFrame, renames columns, and converts it to a dictionary.
    """
    try:
        df = pd.read_csv(file_path)
        df.rename(columns=column_mapping, inplace=True)
        return df.to_dict(orient="records")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []

def filter_by_date(data, date_key, start_date):
    """
    Filters records by a start date, ignoring the time component.
    Prints debug information for records in December only, before filtering.
    """
    start_date = pd.to_datetime(start_date).date()  # Strip time component
    print(f"Debug: Start date for filtering: {start_date}")

    filtered_data = []

    print("Debug: Checking for December records before filtering:")
    for i, record in enumerate(data):
        if date_key in record:
            try:
                record_date = pd.to_datetime(record[date_key]).date()
                record_month = record_date.month

                # Print December dates only
                if record_month == 12:
                    print(f"Record {i}: {record[date_key]} parsed as {record_date}")
                
                # Apply the filtering condition
                if record_date >= start_date:
                    filtered_data.append(record)
            except Exception as e:
                print(f"Error parsing date for record {i}: {record}. Error: {e}")
        else:
            print(f"Record {i}: Missing '{date_key}' key.")

    print(f"Debug: Number of records after filtering: {len(filtered_data)}")
    return filtered_data



# Processing Functions
def consolidate_attendance(attendance_data):
    """
    Consolidates attendance records for each student across multiple locations.

    Args:
        attendance_data (list): List of dictionaries representing attendance records.

    Returns:
        list: Consolidated list of dictionaries, one per student.
    """
    consolidated_data = {}
    for record in attendance_data:
        student_id = record["student_number"]
        if student_id not in consolidated_data:
            consolidated_data[student_id] = {
                "student_number": student_id,
                "name": record.get("name"),
                "grade": record.get("grade"),
                "attending_school": record.get("attending_school"),
                "reporting_school": record.get("reporting_school"),
                "hrs_attended": 0,
                "hrs_possible": 0,
            }
        consolidated_data[student_id]["hrs_attended"] += record.get("hrs_attended", 0)
        consolidated_data[student_id]["hrs_possible"] += record.get("hrs_possible", 0)

    # Calculate and add attendance percentage
    for student_id, data in consolidated_data.items():
        hrs_attended = data["hrs_attended"]
        hrs_possible = data["hrs_possible"]
        data["attendance_percent"] = (
            (hrs_attended / hrs_possible * 100) if hrs_possible > 0 else 0
        )

    # Debug: Print the first 10 attendance percentages
    
    for student_id, data in consolidated_data.items():
        hrs_attended = data["hrs_attended"]
        hrs_possible = data["hrs_possible"]
        attendance_percent = (hrs_attended / hrs_possible * 100) if hrs_possible > 0 else 0
        
        

    return list(consolidated_data.values())

def calculate_adjusted_attendance(attendance_data, med_data, medp_data):
    """
    Calculates adjusted attendance percentages for each student based on MED and MEDP days.
    """

    # Debug: Print the first 10 records of attendance_data
    #print("Debug: First 10 records of attendance_data:")
    for i, record in enumerate(attendance_data):
        #print(record)
        if i >= 9:
            break

    # Aggregate MED and MEDP counts per student
    med_counts = {record["student_number"]: 0 for record in attendance_data}
    medp_counts = {record["student_number"]: 0 for record in attendance_data}

    for record in med_data:
        med_counts[record["student_number"]] = med_counts.get(record["student_number"], 0) + 1

    for record in medp_data:
        medp_counts[record["student_number"]] = medp_counts.get(record["student_number"], 0) + 1

    # Calculate adjusted attendance
    results = {}
    #print("\nDebug: Calculations for each student:")
    for student in attendance_data:
        student_id = student["student_number"]
        starting_attendance = student.get("attendance_percent", 0)  # Already a percentage
        med_days = med_counts.get(student_id, 0)
        medp_days = medp_counts.get(student_id, 0)

        # Calculate the MED/MEDP contribution
        med_contribution_percent = ((med_days + medp_days) / TOTAL_SEMESTER_DAYS) * 100

        # Adjust attendance and cap at 100%
        adjusted_attendance = min(starting_attendance + med_contribution_percent, 100)

        results[student_id] = {
            **student,
            "starting_attendance_percent": starting_attendance,
            "med_full_days": med_days,
            "med_partial_days": medp_days,
            "adjusted_attendance_percent": adjusted_attendance,
        }
        
    
    return results

def generate_building_reports(results_dict, output_dir, school_dict):
    """
    Generates a report for each unique building (mapped school name) in the results dictionary.
    Skipped records with invalid or missing school codes are saved in a separate CSV file.

    Args:
        results_dict (dict): Processed attendance data keyed by student_number.
        output_dir (str): Base output directory for the reports.
        school_dict (dict): Dictionary mapping school codes to school names.

    Returns:
        None
    """
    os.makedirs(output_dir, exist_ok=True)

    skipped_records = []  # List to hold skipped records

    # Map school codes to names in the results
    for student in results_dict.values():
        school_code = student.get("attending_school")

        # Skip records with missing or invalid school codes
        if pd.isna(school_code) or not isinstance(school_code, (int, float)):
            skipped_records.append(student)
            continue

        # Convert school_code to integer for mapping
        try:
            school_code = int(school_code)
        except ValueError:
            skipped_records.append(student)
            continue

        # Map the school code to its name or mark as unknown
        student["attending_school_name"] = school_dict.get(
            school_code, f"Unknown School (Code- {school_code})"
        )

    # Identify unique attending school names
    unique_schools = {
        student["attending_school_name"]
        for student in results_dict.values()
        if "attending_school_name" in student
    }

    for school in unique_schools:
        school_data = [
            student
            for student in results_dict.values()
            if student.get("attending_school_name") == school
        ]

        # Skip empty groups
        if not school_data:
            continue

        # Create folder and save report
        school_folder = os.path.join(output_dir, school.replace(" ", "_"))
        os.makedirs(school_folder, exist_ok=True)

        report_path = os.path.join(school_folder, f"{school}_attendance.csv")
        pd.DataFrame(school_data).to_csv(report_path, index=False)
        print(f"Generated report for school: {school} -> {report_path}")

    # Save skipped records to a separate CSV file
    if skipped_records:
        skipped_path = os.path.join(output_dir, "Skipped_Records.csv")
        pd.DataFrame(skipped_records).to_csv(skipped_path, index=False)
        print(f"Skipped records saved to: {skipped_path}")


def main():
    # File paths
    # Define paths relative to the script location
    base_dir = os.path.dirname(__file__)  # Get the script's directory

    attendance_file = os.path.join(base_dir, "YTD Student Attendance Extract.csv")
    med_file = os.path.join(base_dir, "..", "med.csv")  # Move up one directory
    medp_file = os.path.join(base_dir, "..", "medp.csv")  # Move up one directory
    output_dir = os.path.join(base_dir, "output")

    # School mapping dictionary
    school_dict = {
        1: "School 1",
        2: "School 2",
        3: "School 3",
        4: "School 4",
        5: "School 5",
        6: "School 6",
        7: "School 7",
        8: "School 8",
        9: "School 9",
        10: "School 10",
        11: "School 11",
        12: "School 12",
        13: "School 13",
        14: "School 14",
        15: "School 15",
        16: "School 16",
        17: "School 17",
        18: "School 18",
        19: "School 19",
        20: "School 20",
        21: "School 21",
        22: "alt HS",
        23: "alt Elem",
        24: "techSchool",
        25: "private secondary",
        26: "altprog",
        27: "altprog",
        28: "altprog",
        29: "alt MS",
        30: "Out of Dist Elem",
        31: "ELC",
        32: "ELC",
    }

    # Read and process files
    attendance_data = read_csv_to_dict(attendance_file, attendance_mapping)
    med_data = filter_by_date(read_csv_to_dict(med_file, med_mapping), "date", SEMESTER_START_DATE)
    medp_data = filter_by_date(read_csv_to_dict(medp_file, medp_mapping), "date", SEMESTER_START_DATE)

    # Consolidate attendance data
    consolidated_attendance = consolidate_attendance(attendance_data)

    # Calculate adjusted attendance
    results = calculate_adjusted_attendance(consolidated_attendance, med_data, medp_data)

    # Generate reports for each unique attending school
    generate_building_reports(results, output_dir, school_dict)

if __name__ == "__main__":
    main()

