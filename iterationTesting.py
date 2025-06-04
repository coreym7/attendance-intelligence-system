import unittest
import pandas as pd
import io
import os
import numpy as np
from unittest.mock import patch, mock_open

# Import the functions from your main script
from weeklyAttTrackV2 import read_csv, df_to_dict, prepare_current_week_data, initialize_base_file, clean_base_file, update_base_file
from weeklyAttTrackV2 import read_previous_weeks, consolidate_attendance, input_attendance_data, prime_results, compare_one_week_back, compare_two_weeks_back
from weeklyAttTrackV2 import flag_attendance_issues, process_additional_data, load_additional_data

class TestFirstIteration(unittest.TestCase):
    def setUp(self):
        self.attendance_mapping = {
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

        self.ps_data_mapping = {
            'StudentNumber': 'student_number',
            'DOB': 'dob',
            'AttendingSchool': 'attending_school',
            'SchoolofResidence': 'school_of_residence',
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

        self.mock_current_week_csv = """student_number,Name,Grade,hrs_attended,hrs_absent,hrs_possible,ind_att_percent
1001,John Doe,5,10,2,12,83.33
1002,Jane Smith,5,18,4,22,81.82
1003,Alice Brown,6,20,0,20,100.00
"""

        self.mock_ps_data_csv = """student_number,dob,attending_school,school_of_residence,street,city,state,zip,current_rel_type_code_set_id,is_custodial,lives_with,receives_mail,first_name,middle_name,last_name,email_address,phone_number,phone_number_ext,is_sms,is_preferred
1001,2005-06-01,School A,School A,123 Main St,Townsville,TS,12345,1,1,1,1,John,Doe,Smith,john.smith@example.com,1234567890,,1,1
1002,2006-07-02,School B,School B,456 Oak St,Villagetown,VT,67890,2,0,0,1,Jane,Mary,Smith,jane.smith@example.com,0987654321,,0,0
1003,2007-08-03,School C,School C,789 Pine St,Cityville,CV,12346,3,1,1,0,Alice,B,Johnson,alice.johnson@example.com,5678901234,,1,0
"""

        self.current_week_data = df_to_dict(read_csv(io.StringIO(self.mock_current_week_csv), self.attendance_mapping))
        self.ps_data = df_to_dict(read_csv(io.StringIO(self.mock_ps_data_csv), self.ps_data_mapping))

        # Mock file paths
        self.current_week_file = 'mock_current_week.csv'
        self.base_file = 'mock_base_file.csv'
        self.ps_data_file = 'mock_ps_data.csv'
        self.output_file = 'mock_output.csv'

    @patch("builtins.open", new_callable=mock_open, read_data="mock_current_week_csv")
    @patch("os.path.exists")
    @patch("pandas.DataFrame.to_csv")
    def test_first_iteration(self, mock_to_csv, mock_exists, mock_open):
        # Simulate the base file does not exist
        mock_exists.return_value = False

        # Mock open for reading current week data
        mock_open.return_value = io.StringIO(self.mock_current_week_csv)

        # Step 1: Read and normalize current week data
        current_week_data, one_week_back_data, two_weeks_back_data = input_attendance_data(self.current_week_file, self.base_file, self.attendance_mapping)

        print("Loaded current week data:", current_week_data)  # Debugging step

        # Verify current week data
        self.assertEqual(current_week_data, self.current_week_data)
        self.assertEqual(one_week_back_data, [])
        self.assertEqual(two_weeks_back_data, [])

        # Step 2: Prime the results dictionary
        results = prime_results(current_week_data)

        # Expected initial results
        expected_results = {
            1001: {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'current_week_att_percent': 83.33, 'below_90_1_week': True},
            1002: {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'current_week_att_percent': 81.82, 'below_90_1_week': True},
            1003: {'student_number': 1003, 'name': 'Alice Brown', 'grade': 6, 'current_week_att_percent': 100.0, 'below_90_1_week': False}
        }
        self.assertEqual(results, expected_results)

        # Step 3: Compare one week back
        results = compare_one_week_back(current_week_data, one_week_back_data, results)

        # Verify results after comparing one week back (no changes expected as there's no one week back data)
        self.assertEqual(results, expected_results)

        # Step 4: Compare two weeks back
        results = compare_two_weeks_back(current_week_data, two_weeks_back_data, results)

        # Verify results after comparing two weeks back (no changes expected as there's no two weeks back data)
        self.assertEqual(results, expected_results)

        # Step 5: Load and process additional data
        additional_data = (self.ps_data, {}, {})
        results = process_additional_data(results, additional_data)

        # Expected results after processing additional data
        expected_results_after_ps = {
            1001: {
                'student_number': 1001,
                'name': 'John Doe',
                'grade': 5,
                'current_week_att_percent': 83.33,
                'below_90_1_week': True,
                'dob': '2005-06-01',
                'attending_school': 'School A',
                'school_of_residence': 'School A',
                'street': '123 Main St',
                'city': 'Townsville',
                'state': 'TS',
                'zip': 12345,  # Changed to integer
                'current_rel_type_code_set_id': 1,  # Changed to integer
                'is_custodial': 1,  # Changed to integer
                'lives_with': 1,  # Changed to integer
                'receives_mail': 1,  # Changed to integer
                'first_name': 'John',
                'middle_name': 'Doe',
                'last_name': 'Smith',
                'email_address': 'john.smith@example.com',
                'phone_number': '1234567890',
                'phone_number_ext': np.nan,
                'is_sms': 1,  # Changed to integer
                'is_preferred': 1  # Changed to integer
        },
            1002: {
                'student_number': 1002,
                'name': 'Jane Smith',
                'grade': 5,
                'current_week_att_percent': 81.82,
                'below_90_1_week': True,
                'dob': '2006-07-02',
                'attending_school': 'School B',
                'school_of_residence': 'School B',
                'street': '456 Oak St',
                'city': 'Villagetown',
                'state': 'VT',
                'zip': 67890,  # Changed to integer
                'current_rel_type_code_set_id': 2,  # Changed to integer
                'is_custodial': 0,  # Changed to integer
                'lives_with': 0,  # Changed to integer
                'receives_mail': 1,  # Changed to integer
                'first_name': 'Jane',
                'middle_name': 'Mary',
                'last_name': 'Smith',
                'email_address': 'jane.smith@example.com',
                'phone_number': '0987654321',
                'phone_number_ext': np.nan,
                'is_sms': 0,  # Changed to integer
                'is_preferred': 0  # Changed to integer
            },
            1003: {
                'student_number': 1003,
                'name': 'Alice Brown',
                'grade': 6,
                'current_week_att_percent': 100.0,
                'below_90_1_week': False,
                'dob': '2007-08-03',
                'attending_school': 'School C',
                'school_of_residence': 'School C',
                'street': '789 Pine St',
                'city': 'Cityville',
                'state': 'CV',
                'zip': 12346,  # Changed to integer
                'current_rel_type_code_set_id': 3,  # Changed to integer
                'is_custodial': 1,  # Changed to integer
                'lives_with': 1,  # Changed to integer
                'receives_mail': 0,  # Changed to integer
                'first_name': 'Alice',
                'middle_name': 'B',
                'last_name': 'Johnson',
                'email_address': 'alice.johnson@example.com',
                'phone_number': '5678901234',
                'phone_number_ext': np.nan,
                'is_sms': 1,  # Changed to integer
                'is_preferred': 0  # Changed to integer
            }
        }
        self.assertEqual(results, expected_results_after_ps)

        # Step 6: Update the base file with the current week data
        update_base_file(current_week_data, self.base_file, self.attendance_mapping)

        # Verify that the base file was written correctly
        written_data = io.StringIO(mock_open().read_data)
        updated_df = pd.read_csv(written_data)
        expected_updated_df = pd.DataFrame([
            {'student_number': 1001, 'name': 'John Doe', 'grade': 5, 'hrs_attended': 10, 'hrs_absent': 2, 'hrs_possible': 12, 'ind_att_percent': 83.33, 'weekly_value': -1},
            {'student_number': 1002, 'name': 'Jane Smith', 'grade': 5, 'hrs_attended': 18, 'hrs_absent': 4, 'hrs_possible': 22, 'ind_att_percent': 81.82, 'weekly_value': -1},
            {'student_number': 1003, 'name': 'Alice Brown', 'grade': 6, 'hrs_attended': 20, 'hrs_absent': 0, 'hrs_possible': 20, 'ind_att_percent': 100.0, 'weekly_value': -1}
        ])
        pd.testing.assert_frame_equal(updated_df, expected_updated_df)

        # Step 7: Write results to CSV
        results_list = list(results.values())
        results_df = pd.DataFrame(results_list)
        results_output = io.StringIO()
        results_df.to_csv(results_output, index=False)

        # Verify that the output file was written correctly
        written_output_df = pd.read_csv(io.StringIO(results_output.getvalue()))
        pd.testing.assert_frame_equal(written_output_df, results_df)

if __name__ == '__main__':
    unittest.main(verbosity=2)
