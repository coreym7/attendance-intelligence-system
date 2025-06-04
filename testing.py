import unittest
import pandas as pd
import io
import os
from unittest.mock import patch, mock_open

# Import the functions from your main script
from weeklyAttTrackV2 import read_csv, df_to_dict, prepare_current_week_data, initialize_base_file, clean_base_file, update_base_file
from weeklyAttTrackV2 import read_previous_weeks, consolidate_attendance, input_attendance_data,prime_results, compare_one_week_back, compare_two_weeks_back
from weeklyAttTrackV2 import flag_attendance_issues,process_additional_data

class TestCSVFunctions(unittest.TestCase):

    def setUp(self):
        # Mock CSV content for the current week
        self.current_week_csv_content = """Count,Reporting School,Attending School,MOSIS ID,Student Number,Name,Grade,Hrs Attended,Hrs Absent,Hrs Possible,Ind Att %,Segment,Tot Hrs for Period,Att Pts,Adj Prop Wt
1,School A,School B,12345,1001,John Doe,5,20,2,22,90.91,1,22,20,1
2,School A,School B,12346,1002,Jane Smith,5,18,4,22,81.82,1,22,18,1"""
        
        self.column_mapping = {
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

    def test_read_csv(self):
        # Use StringIO to simulate file I/O
        mock_csv_file = io.StringIO(self.current_week_csv_content)
        
        # Read the CSV using the function
        df = pd.read_csv(mock_csv_file)
        df = df.rename(columns=self.column_mapping)
        
        expected_columns = ['count', 'reporting_school', 'attending_school', 'mosis_id', 'student_number', 'name', 'grade', 'hrs_attended', 'hrs_absent', 'hrs_possible', 'ind_att_percent', 'segment', 'total_hrs_period', 'att_pts', 'adj_prop_wt']
        self.assertListEqual(list(df.columns), expected_columns)
        self.assertEqual(len(df), 2)

    def test_df_to_dict(self):
        # Use StringIO to simulate file I/O
        mock_csv_file = io.StringIO(self.current_week_csv_content)
        
        # Read the CSV using the function
        df = read_csv(mock_csv_file, self.column_mapping)
        
        # Convert DataFrame to dictionary
        dict_data = df_to_dict(df)
        
        # Verify the length and content of the dictionary
        self.assertEqual(len(dict_data), 2)
        self.assertEqual(dict_data[0]['name'], 'John Doe')
        self.assertEqual(dict_data[1]['name'], 'Jane Smith')

    def test_prepare_current_week_data(self):
        # Use StringIO to simulate file I/O
        mock_csv_file = io.StringIO(self.current_week_csv_content)
        
        # Read the CSV using the function
        df = read_csv(mock_csv_file, self.column_mapping)
        
        # Convert DataFrame to dictionary
        dict_data = df_to_dict(df)
        
        # Prepare current week's data
        prepared_df = prepare_current_week_data(dict_data)
        
        # Verify the content and weekly_value
        self.assertIn('weekly_value', prepared_df.columns)
        self.assertTrue((prepared_df['weekly_value'] == -1).all())

    def test_initialize_base_file(self):
        # Convert the CSV content to dictionary
        mock_csv_file = io.StringIO(self.current_week_csv_content)
        df = read_csv(mock_csv_file, self.column_mapping)
        current_week_data = df_to_dict(df)

        # Mock the open function and to_csv method
        m = mock_open()
        with patch("builtins.open", m):
            with patch.object(pd.DataFrame, "to_csv") as mock_to_csv:
                initialize_base_file(current_week_data, "base_file.csv")
                mock_to_csv.assert_called_once_with("base_file.csv", index=False)

class TestCleanBaseFile(unittest.TestCase):

    def setUp(self):
        # Mock DataFrame content
        self.data = {
            'student_number': [1001, 1002, 1003, 1004],
            'name': ['John Doe', 'Jane Smith', 'Alice Johnson', 'Bob Brown'],
            'weekly_value': [-1, -2, -3, -3],
            'total_hrs_attended': [20, 18, 15, 17],
            'total_hrs_absent': [2, 4, 5, 3],
            'total_hrs_possible': [22, 22, 20, 20]
        }
        self.df = pd.DataFrame(self.data)

    def test_clean_base_file(self):
        # Apply the clean_base_file function
        cleaned_df = clean_base_file(self.df)
        
        # Expected DataFrame after cleaning
        expected_data = {
            'student_number': [1001, 1002],
            'name': ['John Doe', 'Jane Smith'],
            'weekly_value': [-1, -2],
            'total_hrs_attended': [20, 18],
            'total_hrs_absent': [2, 4],
            'total_hrs_possible': [22, 22]
        }
        expected_df = pd.DataFrame(expected_data)
        
        # Verify the cleaned DataFrame
        pd.testing.assert_frame_equal(cleaned_df, expected_df)
    
class TestUpdateBaseFile(unittest.TestCase):

    def setUp(self):
        # Create mock CSV content for the base file
        self.base_file_content = """count,reporting_school,attending_school,mosis_id,student_number,name,grade,hrs_attended,hrs_absent,hrs_possible,ind_att_percent,segment,total_hrs_period,att_pts,adj_prop_wt,weekly_value
1,School A,School B,12345,1001,John Doe,5,20,2,22,90.91,1,22,20,1,-1
1,School A,School B,12346,1002,Jane Smith,5,18,4,22,81.82,1,22,18,1,-2
1,School A,School B,12347,1003,Alice Johnson,5,15,5,20,75.0,1,20,15,1,-2"""
        
        # Create mock CSV content for the current week
        self.current_week_content = """count,reporting_school,attending_school,mosis_id,student_number,name,grade,hrs_attended,hrs_absent,hrs_possible,ind_att_percent,segment,total_hrs_period,att_pts,adj_prop_wt
1,School A,School B,12348,1004,Bob Brown,6,17,3,20,85.0,1,20,17,1"""
        
        self.column_mapping = {
            'count': 'count',
            'reporting_school': 'reporting_school',
            'attending_school': 'attending_school',
            'mosis_id': 'mosis_id',
            'student_number': 'student_number',
            'name': 'name',
            'grade': 'grade',
            'hrs_attended': 'hrs_attended',
            'hrs_absent': 'hrs_absent',
            'hrs_possible': 'hrs_possible',
            'ind_att_percent': 'ind_att_percent',
            'segment': 'segment',
            'total_hrs_period': 'total_hrs_period',
            'att_pts': 'att_pts',
            'adj_prop_wt': 'adj_prop_wt'
        }

        # Create the test files
        with open('test_base_file.csv', 'w') as f:
            f.write(self.base_file_content)
        with open('test_current_week.csv', 'w') as f:
            f.write(self.current_week_content)

    def tearDown(self):
        # Remove the test files
        os.remove('test_base_file.csv')
        os.remove('test_current_week.csv')

    def test_update_base_file_existing(self):
        # Read the current week file
        current_week_df = read_csv('test_current_week.csv', self.column_mapping)
        current_week_data = df_to_dict(current_week_df)

        # Call the function to update the base file
        update_base_file(current_week_data, 'test_base_file.csv', self.column_mapping)
        
        # Verify the updated DataFrame
        updated_df = pd.read_csv('test_base_file.csv')

        

        # Expected data after update
        expected_data = {
            'count': [1, 1],
            'reporting_school': ['School A', 'School A'],
            'attending_school': ['School B', 'School B'],
            'mosis_id': [12345, 12348],
            'student_number': [1001, 1004],
            'name': ['John Doe', 'Bob Brown'],
            'grade': [5, 6],
            'hrs_attended': [20, 17],
            'hrs_absent': [2, 3],
            'hrs_possible': [22, 20],
            'ind_att_percent': [90.91, 85.0],
            'segment': [1, 1],
            'total_hrs_period': [22, 20],
            'att_pts': [20, 17],
            'adj_prop_wt': [1, 1],
            'weekly_value': [-2, -1]
        }
        expected_df = pd.DataFrame(expected_data)

       

        # Fill NaNs with None for comparison
        updated_df = updated_df.where(pd.notnull(updated_df), None)

        # Compare the updated DataFrame with the expected DataFrame
        pd.testing.assert_frame_equal(updated_df.reset_index(drop=True), expected_df.reset_index(drop=True))
            
class TestReadPreviousWeeks(unittest.TestCase):

    def setUp(self):
        # Create mock CSV content for the base file with minimal columns
        self.base_file_content = """name,grade,school,weekly_value
John Doe,5,School A,-1
Jane Smith,5,School A,-2
Alice Johnson,5,School A,-2
Bob Brown,6,School A,-1"""
        
        self.column_mapping = {
            'name': 'name',
            'grade': 'grade',
            'school': 'school',
            'weekly_value': 'weekly_value'
        }

        # Create the test file
        with open('test_base_file.csv', 'w') as f:
            f.write(self.base_file_content)

    def tearDown(self):
        # Remove the test file
        os.remove('test_base_file.csv')

    def test_read_previous_weeks(self):
        # Call the function to read previous weeks
        one_week_prior_df, two_weeks_prior_df = read_previous_weeks('test_base_file.csv', self.column_mapping)
        
        # Expected data for one week prior
        expected_one_week_prior_data = {
            'name': ['John Doe', 'Bob Brown'],
            'grade': [5, 6],
            'school': ['School A', 'School A'],
            'weekly_value': [-1, -1]
        }
        expected_one_week_prior_df = pd.DataFrame(expected_one_week_prior_data)

        # Expected data for two weeks prior
        expected_two_weeks_prior_data = {
            'name': ['Jane Smith', 'Alice Johnson'],
            'grade': [5, 5],
            'school': ['School A', 'School A'],
            'weekly_value': [-2, -2]
        }
        expected_two_weeks_prior_df = pd.DataFrame(expected_two_weeks_prior_data)

        # Verify the DataFrames
        pd.testing.assert_frame_equal(one_week_prior_df.reset_index(drop=True), expected_one_week_prior_df.reset_index(drop=True))
        pd.testing.assert_frame_equal(two_weeks_prior_df.reset_index(drop=True), expected_two_weeks_prior_df.reset_index(drop=True))

class TestConsolidateAttendance(unittest.TestCase):

    def setUp(self):
        self.attendance_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'hrs_attended': 10, 'hrs_absent': 2, 'hrs_possible': 12},
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'hrs_attended': 10, 'hrs_absent': 2, 'hrs_possible': 10},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'hrs_attended': 18, 'hrs_absent': 4, 'hrs_possible': 22},
            {'student_number': 1003, 'name': 'Emily White', 'grade': 6, 'hrs_attended': 20, 'hrs_absent': 0, 'hrs_possible': 20}
        ]

    def test_consolidate_attendance(self):
        expected_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'hrs_attended': 20, 'hrs_absent': 4, 'hrs_possible': 22, 'ind_att_percent': 90.91},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'hrs_attended': 18, 'hrs_absent': 4, 'hrs_possible': 22, 'ind_att_percent': 81.82},
            {'student_number': 1003, 'name': 'Emily White', 'grade': 6, 'hrs_attended': 20, 'hrs_absent': 0, 'hrs_possible': 20, 'ind_att_percent': 100.00}
        ]
        
        consolidated_data = consolidate_attendance(self.attendance_data)
        
        
        
        # Verify the consolidated data
        self.assertEqual(consolidated_data, expected_data)

class TestInputAttendanceData(unittest.TestCase):

    def setUp(self):
        # Create mock CSV content for the base file
        self.base_file_content = """student_number,name,grade,hrs_attended,hrs_absent,hrs_possible,weekly_value
1001,John Doe,5,20,2,22,-1
1004,Bob Brown,6,17,3,20,-1
1002,Jane Smith,5,18,4,22,-2
1003,Alice Johnson,5,15,5,20,-2"""

        # Create mock CSV content for the current week
        self.current_week_content = """student_number,name,grade,hrs_attended,hrs_absent,hrs_possible
1001,John Doe,5,10,2,12
1005,Emily White,6,18,2,20"""

        self.column_mapping = {
            'student_number': 'student_number',
            'name': 'name',
            'grade': 'grade',
            'hrs_attended': 'hrs_attended',
            'hrs_absent': 'hrs_absent',
            'hrs_possible': 'hrs_possible'
        }

        # Create the test files
        with open('test_base_file.csv', 'w') as f:
            f.write(self.base_file_content)
        with open('test_current_week.csv', 'w') as f:
            f.write(self.current_week_content)

    def tearDown(self):
        # Remove the test files
        os.remove('test_base_file.csv')
        os.remove('test_current_week.csv')

    def test_input_attendance_data_with_full_base_file(self):
        # Read the current week file
        current_week_data, one_week_prior_data, two_weeks_prior_data = input_attendance_data('test_current_week.csv', 'test_base_file.csv', self.column_mapping)
        
        # Expected data
        expected_current_week_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'hrs_attended': 10, 'hrs_absent': 2, 'hrs_possible': 12, 'ind_att_percent': 83.33},
            {'student_number': 1005, 'name': 'Emily White', 'grade': 6, 'hrs_attended': 18, 'hrs_absent': 2, 'hrs_possible': 20, 'ind_att_percent': 90.0}
        ]

        expected_one_week_prior_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'hrs_attended': 20, 'hrs_absent': 2, 'hrs_possible': 22, 'weekly_value': -1},
            {'student_number': 1004, 'name': 'Bob Brown', 'grade': 6, 'hrs_attended': 17, 'hrs_absent': 3, 'hrs_possible': 20, 'weekly_value': -1}
        ]

        expected_two_weeks_prior_data = [
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'hrs_attended': 18, 'hrs_absent': 4, 'hrs_possible': 22, 'weekly_value': -2},
            {'student_number': 1003, 'name': 'Alice Johnson', 'grade': 5, 'hrs_attended': 15, 'hrs_absent': 5, 'hrs_possible': 20, 'weekly_value': -2}
        ]
        
        

        # Verify the data
        self.assertEqual(current_week_data, expected_current_week_data)
        self.assertEqual(one_week_prior_data, expected_one_week_prior_data)
        self.assertEqual(two_weeks_prior_data, expected_two_weeks_prior_data)

class TestPrimeResults(unittest.TestCase):
    def setUp(self):
        self.current_week_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'hrs_attended': 10, 'hrs_absent': 2, 'hrs_possible': 12, 'ind_att_percent': 83.33},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'hrs_attended': 18, 'hrs_absent': 4, 'hrs_possible': 22, 'ind_att_percent': 81.82}
        ]

    def test_prime_results(self):
        expected_results = {
            1001: {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'current_week_att_percent': 83.33, 'below_90_1_week': True},
            1002: {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'current_week_att_percent': 81.82, 'below_90_1_week': True}
        }
        results = prime_results(self.current_week_data)
        self.assertEqual(results, expected_results)

class TestCompareOneWeekBack(unittest.TestCase):
    def setUp(self):
        self.current_week_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'ind_att_percent': 83.33},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'ind_att_percent': 81.82},
        ]
        
        self.one_week_back_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'ind_att_percent': 66.67},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'ind_att_percent': 72.73},
        ]
        
        self.initial_results = {
            1001: {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'current_week_att_percent': 83.33, 'below_90_1_week': True},
            1002: {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'current_week_att_percent': 81.82, 'below_90_1_week': True},
        }
        
    def test_compare_one_week_back(self):
        expected_results = {
            1001: {
                'student_number': 1001,
                'name': 'John Doe',
                'grade': 5,
                'current_week_att_percent': 83.33,
                'below_90_1_week': True,
                'one_week_back_percent': 66.67,
                'below_90_2_weeks': True,
                'trend_1_week': 'Up'
            },
            1002: {
                'student_number': 1002,
                'name': 'Jane Smith',
                'grade': 5,
                'current_week_att_percent': 81.82,
                'below_90_1_week': True,
                'one_week_back_percent': 72.73,
                'below_90_2_weeks': True,
                'trend_1_week': 'Up'
            }
        }
        
        results = compare_one_week_back(self.current_week_data, self.one_week_back_data, self.initial_results)
        self.assertEqual(results, expected_results)
   

class TestCompareTwoWeeksBack(unittest.TestCase):
    def setUp(self):
        self.current_week_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'ind_att_percent': 83.33},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'ind_att_percent': 81.82},
            {'student_number': 1003, 'name': 'Alice Brown', 'grade': 6, 'ind_att_percent': 85.00},  # Below 90% in current week only
            {'student_number': 1004, 'name': 'Bob White', 'grade': 6, 'ind_att_percent': 78.00},   # Below 90% in current and previous week
            {'student_number': 1005, 'name': 'Charlie Black', 'grade': 6, 'ind_att_percent': 91.00}, # Above 90% in previous weeks, below in current
        ]
        
        self.one_week_back_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'ind_att_percent': 66.67},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'ind_att_percent': 72.73},
            {'student_number': 1003, 'name': 'Alice Brown', 'grade': 6, 'ind_att_percent': 95.00},
            {'student_number': 1004, 'name': 'Bob White', 'grade': 6, 'ind_att_percent': 85.00},
            {'student_number': 1005, 'name': 'Charlie Black', 'grade': 6, 'ind_att_percent': 92.00},
        ]
        
        self.two_weeks_back_data = [
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'ind_att_percent': 50.00},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'ind_att_percent': 75.00},
            {'student_number': 1003, 'name': 'Alice Brown', 'grade': 6, 'ind_att_percent': 92.00},
            {'student_number': 1004, 'name': 'Bob White', 'grade': 6, 'ind_att_percent': 89.00},
            {'student_number': 1005, 'name': 'Charlie Black', 'grade': 6, 'ind_att_percent': 93.00},
        ]
        
        self.initial_results = {
            1001: {
                'student_number': 1001,
                'name': 'John Doe',
                'grade': 5,
                'current_week_att_percent': 83.33,
                'below_90_1_week': True,
                'one_week_back_percent': 66.67,
                'below_90_2_weeks': True,
                'trend_1_week': 'Up'
            },
            1002: {
                'student_number': 1002,
                'name': 'Jane Smith',
                'grade': 5,
                'current_week_att_percent': 81.82,
                'below_90_1_week': True,
                'one_week_back_percent': 72.73,
                'below_90_2_weeks': True,
                'trend_1_week': 'Up'
            },
            1003: {
                'student_number': 1003,
                'name': 'Alice Brown',
                'grade': 6,
                'current_week_att_percent': 85.00,
                'below_90_1_week': True,
                'one_week_back_percent': 95.00,
                'below_90_2_weeks': False,
                'trend_1_week': 'Down'
            },
            1004: {
                'student_number': 1004,
                'name': 'Bob White',
                'grade': 6,
                'current_week_att_percent': 78.00,
                'below_90_1_week': True,
                'one_week_back_percent': 85.00,
                'below_90_2_weeks': True,
                'trend_1_week': 'Down'
            },
            1005: {
                'student_number': 1005,
                'name': 'Charlie Black',
                'grade': 6,
                'current_week_att_percent': 91.00,
                'below_90_1_week': False,
                'one_week_back_percent': 92.00,
                'below_90_2_weeks': False,
                'trend_1_week': 'Down'
            }
        }
        
    def test_compare_two_weeks_back(self):
        expected_results = {
            1001: {
                'student_number': 1001,
                'name': 'John Doe',
                'grade': 5,
                'current_week_att_percent': 83.33,
                'below_90_1_week': True,
                'one_week_back_percent': 66.67,
                'below_90_2_weeks': True,
                'trend_1_week': 'Up',
                'two_weeks_back_percent': 50.00,
                'below_90_3_weeks': True,
                'trend_2_weeks': 'Up'
            },
            1002: {
                'student_number': 1002,
                'name': 'Jane Smith',
                'grade': 5,
                'current_week_att_percent': 81.82,
                'below_90_1_week': True,
                'one_week_back_percent': 72.73,
                'below_90_2_weeks': True,
                'trend_1_week': 'Up',
                'two_weeks_back_percent': 75.00,
                'below_90_3_weeks': True,
                'trend_2_weeks': 'Up'
            },
            1003: {
                'student_number': 1003,
                'name': 'Alice Brown',
                'grade': 6,
                'current_week_att_percent': 85.00,
                'below_90_1_week': True,
                'one_week_back_percent': 95.00,
                'below_90_2_weeks': False,
                'trend_1_week': 'Down',
                'two_weeks_back_percent': 92.00,
                'below_90_3_weeks': False,
                'trend_2_weeks': 'Down'
            },
            1004: {
                'student_number': 1004,
                'name': 'Bob White',
                'grade': 6,
                'current_week_att_percent': 78.00,
                'below_90_1_week': True,
                'one_week_back_percent': 85.00,
                'below_90_2_weeks': True,
                'trend_1_week': 'Down',
                'two_weeks_back_percent': 89.00,
                'below_90_3_weeks': True,
                'trend_2_weeks': 'Down'
            },
            1005: {
                'student_number': 1005,
                'name': 'Charlie Black',
                'grade': 6,
                'current_week_att_percent': 91.00,
                'below_90_1_week': False,
                'one_week_back_percent': 92.00,
                'below_90_2_weeks': False,
                'trend_1_week': 'Down',
                'two_weeks_back_percent': 93.00,
                'below_90_3_weeks': False,
                'trend_2_weeks': 'Down'
            }
        }
        
        results = compare_two_weeks_back(self.current_week_data, self.two_weeks_back_data, self.initial_results)
        self.assertEqual(results, expected_results)

class TestAdditionalDataProcessing(unittest.TestCase):
    
    def setUp(self):
        # Creating mock PowerSchool data
        self.ps_data = [
            {
                'student_number': 1001,
                'dob': '2005-06-01',
                'attending_school': 'School A',
                'school_of_residence': 'School B',
                'street': '123 Main St',
                'city': 'Townsville',
                'state': 'TS',
                'zip': '12345',
                'current_rel_type_code_set_id': 1,
                'is_custodial': 1,
                'lives_with': 1,
                'receives_mail': 1,
                'first_name': 'John',
                'middle_name': 'D',
                'last_name': 'Smith',
                'email_address': 'john.smith@example.com',
                'phone_number': '1234567890',
                'phone_number_ext': '',
                'is_sms': 1,
                'is_preferred': 1
            },
            {
                'student_number': 1002,
                'dob': '2006-07-02',
                'attending_school': 'School C',
                'school_of_residence': 'School D',
                'street': '789 Oak St',
                'city': 'Villagetown',
                'state': 'VT',
                'zip': '67890',
                'current_rel_type_code_set_id': 2,
                'is_custodial': 0,
                'lives_with': 0,
                'receives_mail': 1,
                'first_name': 'Jane',
                'middle_name': 'M',
                'last_name': 'Doe',
                'email_address': 'jane.doe@example.com',
                'phone_number': '0987654321',
                'phone_number_ext': '',
                'is_sms': 0,
                'is_preferred': 0
            }
        ]

        # Creating mock Probation data
        self.pa_data = [
            {
                'student_number': 1001,
                'current_status': 'Active',
                'end_date': '2024-12-31',
                'notes': 'On probation'
            },
            {
                'student_number': 1002,
                'current_status': 'Inactive',
                'end_date': '2024-01-01',
                'notes': 'Completed program'
            }
        ]

        # Sample results dictionary to process
        self.results_dict = {
            1001: {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'current_week_att_percent': 85, 'below_90_1_week': True},
            1002: {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'current_week_att_percent': 92, 'below_90_1_week': False}
        }

    def test_process_additional_data(self):
        # Process the additional data
        results = process_additional_data(self.results_dict, (self.ps_data, self.pa_data))
        
        # Expected results after processing
        expected_results = {
            1001: {
                'student_number': 1001,
                'name': 'John Doe',
                'grade': 5,
                'current_week_att_percent': 85,
                'below_90_1_week': True,
                'dob': '2005-06-01',
                'attending_school': 'School A',
                'school_of_residence': 'School B',
                'street': '123 Main St',
                'city': 'Townsville',
                'state': 'TS',
                'zip': '12345',
                'current_rel_type_code_set_id': 1,
                'is_custodial': 1,
                'lives_with': 1,
                'receives_mail': 1,
                'first_name': 'John',
                'middle_name': 'D',
                'last_name': 'Smith',
                'email_address': 'john.smith@example.com',
                'phone_number': '1234567890',
                'phone_number_ext': '',
                'is_sms': 1,
                'is_preferred': 1,
                'current_status': 'Active',
                'end_date': '2024-12-31',
                'notes': 'On probation'
            },
            1002: {
                'student_number': 1002,
                'name': 'Jane Smith',
                'grade': 5,
                'current_week_att_percent': 92,
                'below_90_1_week': False,
                'dob': '2006-07-02',
                'attending_school': 'School C',
                'school_of_residence': 'School D',
                'street': '789 Oak St',
                'city': 'Villagetown',
                'state': 'VT',
                'zip': '67890',
                'current_rel_type_code_set_id': 2,
                'is_custodial': 0,
                'lives_with': 0,
                'receives_mail': 1,
                'first_name': 'Jane',
                'middle_name': 'M',
                'last_name': 'Doe',
                'email_address': 'jane.doe@example.com',
                'phone_number': '0987654321',
                'phone_number_ext': '',
                'is_sms': 0,
                'is_preferred': 0,
                'current_status': 'Inactive',
                'end_date': '2024-01-01',
                'notes': 'Completed program'
            }
        }

        # Check for the fields we care about
        for student_id, expected_values in expected_results.items():
            for key, expected_value in expected_values.items():
                self.assertEqual(results[student_id][key], expected_value, f"Mismatch in {key} for student {student_id}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
