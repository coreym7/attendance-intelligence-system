import unittest
import os
import pandas as pd
from shutil import rmtree
from unittest.mock import patch

# Assuming the functions from generateLetters.py are imported
from generateLetters import read_final_report, generate_letters_by_building

class TestGenerateLetters(unittest.TestCase):

    def setUp(self):
        """
        Setup mock data for the unit test, simulating final_report.csv content.
        """
        # Mock DataFrame to simulate final_report.csv
        self.mock_final_report = pd.DataFrame({
            'student_number': ['12345', '67890', '11223'],
            'full_name': ['John Doe', 'Jane Smith', 'Jim Brown'],
            'grade': ['10', '11', '12'],
            'school_of_residence': ['School3', 'School1', 'School2'],
            'current_week_att_percent': [95.5, 88.3, 92.7]
        })
        
        # Path for test outputs
        self.output_dir = os.path.join(os.getcwd(), 'test_output')
        
        # Building group mapping
        self.building_group_mapping = {
            'School1 - Bethany Hernandez-Rice': ['School1'],
            'School2 - Chelsey Sollars': ['School2'],
            'School3 - Angela Hernandez': ['School3']
        }

        # Create the output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    @patch('generateLetters.pd.read_csv')
    def test_read_final_report_and_generate_letters(self, mock_read_csv):
        """
        Test the read_final_report and generate_letters_by_building functions.
        """
        # Mock the read_csv function to return the mock_final_report DataFrame
        mock_read_csv.return_value = self.mock_final_report

        # Call the read_final_report function
        results = read_final_report(os.path.join(self.output_dir, 'final_report.csv'))

        # Verify that results dictionary was constructed correctly
        self.assertIn('12345', results)
        self.assertIn('67890', results)
        self.assertIn('11223', results)

        # Verify some key values from the results
        self.assertEqual(results['12345']['full_name'], 'John Doe')
        self.assertEqual(results['67890']['school_of_residence'], 'School1')
        self.assertEqual(results['11223']['current_week_att_percent'], 92.7)

        # Call the generate_letters_by_building function
        generate_letters_by_building(results, self.output_dir, self.building_group_mapping, max_pages=None)

        # Check that directories are created for each school
        School1_path = os.path.join(self.output_dir, 'School 1 - Team 1')
        School2_path = os.path.join(self.output_dir, 'School 2 - Team 2')
        School3_path = os.path.join(self.output_dir, 'School3 - Team 3')

        self.assertTrue(os.path.exists(School1_path), "School1 directory not created.")
        self.assertTrue(os.path.exists(School2_path), "School2 directory not created.")
        self.assertTrue(os.path.exists(School3_path), "School3 directory not created.")

        # Check that a Word document was created in each directory
        self.assertTrue(os.path.exists(os.path.join(School1_path, "letters_part1.docx")), "School1 letter not created.")
        self.assertTrue(os.path.exists(os.path.join(School2_path, "letters_part1.docx")), "School2 letter not created.")
        self.assertTrue(os.path.exists(os.path.join(School3_path, "letters_part1.docx")), "School3 letter not created.")

    def tearDown(self):
        """
        Clean up any files created during the test.
        """
        # Remove the test output directory and its contents after the test completes
        if os.path.exists(self.output_dir):
            rmtree(self.output_dir)


if __name__ == '__main__':
    unittest.main()
