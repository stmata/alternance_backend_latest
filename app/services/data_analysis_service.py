import pandas as pd
import numpy as np
from ydata_profiling import ProfileReport
from io import StringIO

class DataAnalysisService:
    """
    DataAnalysisService class for analyzing data from a CSV file.

    This class allows you to load data from a CSV file, analyze the data, and
    retrieve statistical information about the dataset.

    Attributes:
        data (pandas.DataFrame): Data loaded from the CSV file.

    Methods:
        analyze_data(): Performs a complete analysis of the dataset and returns the results.
        get_stats_overview(): Retrieves the overall statistics about the dataset.
        get_variable_info(): Retrieves detailed information about each variable.
        get_missing_values(): Retrieves the missing values for each variable.
        get_correlations(): Calculates the correlations between the numeric variables.
        convert_to_native(): Converts NumPy types to native Python types.
    """
    def __init__(self, csv_content: str):
        try:
            self.data = pd.read_csv(StringIO(csv_content))
        except pd.errors.EmptyDataError:
            raise ValueError("The CSV file is empty or malformed.")
        except Exception as e:
            raise ValueError(f"Error while loading CSV data: {str(e)}")

    def analyze_data(self):
        """
        Performs a complete analysis of the dataset and returns the results.

        Raises:
            ValueError: In case of an error during data analysis.
            Exception: In case of a general error during data analysis.

        Returns:
            dict: Dictionary containing the results of the data analysis.
        """
        try:
            # Generate a comprehensive report using ydata_profiling
            profile = ProfileReport(self.data, title="Data Analysis Report", explorative=True)

            # Retrieve the detailed information
            stats_overview = self.get_stats_overview()
            variable_info = self.get_variable_info()
            missing_values = self.get_missing_values()

            # Retrieve the correlations only if there are numeric columns
            correlations = self.get_correlations()

            # Convert NumPy types to native types before returning the data
            return {
                "overview": self.convert_to_native(stats_overview),
                "variables": self.convert_to_native(variable_info),
                "missing_values": self.convert_to_native(missing_values),
                "correlations": self.convert_to_native(correlations),
            }

        except ValueError as ve:
            raise ValueError(f"Error during data analysis: {str(ve)}")
        except Exception as e:
            raise ValueError(f"An error occurred during data analysis: {str(e)}")

    def get_stats_overview(self):
        """
        Retrieves the overall statistics about the dataset.

        Raises:
            ValueError: In case of an error while retrieving the overall statistics.

        Returns:
            dict: Dictionary containing the overall statistics.
        """
        try:
            stats = {
                "Number of variables": self.data.shape[1],
                "Number of observations": self.data.shape[0],
                "Missing cells": int(self.data.isnull().sum().sum()),  # Conversion to native
                "Missing cells (%)": float((self.data.isnull().sum().sum() / (self.data.shape[0] * self.data.shape[1])) * 100),
                "Duplicate rows": int(self.data.duplicated().sum()),  # Conversion to native
                "Duplicate rows (%)": float((self.data.duplicated().sum() / self.data.shape[0]) * 100),
                "Total size in memory": int(self.data.memory_usage(deep=True).sum()),  # Conversion to native
                "Average record size in memory": float(self.data.memory_usage(deep=True).mean()),  # Conversion to native
            }
            return stats
        except Exception as e:
            raise ValueError(f"Error while retrieving the overall statistics: {str(e)}")

    def get_variable_info(self):
        """
        Retrieves the detailed information about each variable.

        Raises:
            ValueError: In case of an error while retrieving the variable information.

        Returns:
            dict: Dictionary containing the information about each variable.
        """
        try:
            variable_info = {}
            for col in self.data.columns:
                variable_info[col] = {
                    "Type": str(self.data[col].dtype),
                    "Distinct": int(self.data[col].nunique()),  # Conversion to native
                    "Missing": int(self.data[col].isnull().sum()),  # Conversion to native
                    "Missing (%)": float((self.data[col].isnull().sum() / self.data.shape[0]) * 100),
                    "Memory size": int(self.data[col].memory_usage(deep=True)),  # Conversion to native
                    "Top": self.data[col].mode()[0] if not self.data[col].mode().empty else None,
                }
            return variable_info
        except Exception as e:
            raise ValueError(f"Error while retrieving the variable information: {str(e)}")

    def get_missing_values(self):
        """
        Retrieves the missing values for each variable.

        Raises:
            ValueError: In case of an error while retrieving the missing values.

        Returns:
            dict: Dictionary containing the missing values for each variable.
        """
        try:
            missing_data = self.data.isnull().sum().to_dict()
            return missing_data
        except Exception as e:
            raise ValueError(f"Error while retrieving the missing values: {str(e)}")

    def get_correlations(self):
        """
        Calculates the correlations between the numeric variables.

        Raises:
            ValueError: In case of an error while generating the correlations.

        Returns:
            dict: Dictionary containing the correlations between the numeric variables.
        """
        try:
            numeric_data = self.data.select_dtypes(include=[float, int])

            if numeric_data.empty:
                return {"message": "No numeric columns available for correlations."}

            correlations = numeric_data.corr().to_dict()
            return correlations
        except Exception as e:
            raise ValueError(f"Error while generating the correlations: {str(e)}")

    def convert_to_native(self, data):
        """
        Converts NumPy types to native Python types to ensure
        compatibility with the JSON format.

        Args:
            data (dict, list, numpy.integer, numpy.floating, numpy.ndarray): Data to convert.

        Returns:
            dict, list, int, float, list: Data converted to native Python types.
        """
        if isinstance(data, dict):
            return {k: self.convert_to_native(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_to_native(i) for i in data]
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data