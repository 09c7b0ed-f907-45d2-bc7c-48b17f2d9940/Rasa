"""Monolithic module for hospital statistical analysis.

This module provides a complete, self-contained solution for comparing
door-to-needle times between two hospitals using statistical tests.
Designed for easy integration into other projects (e.g., Rasa chatbots).

Usage Example
-------------
    from src.util.hospital_statistics import HospitalStatistics
    
    # Initialize analyzer
    stats = HospitalStatistics()
    
    # Generate and analyze synthetic data
    result = stats.run_analysis(n_rows=50, random_state=42)
    
    # Get formatted results
    print(result.get_summary())
    
    # Or use with real data
    import pandas as pd
    df1 = pd.read_csv('hospital1.csv')
    df2 = pd.read_csv('hospital2.csv')
    result = stats.run_analysis_from_dataframes(df1, df2)
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import NamedTuple, Literal, Optional, Tuple
from datetime import datetime
from pathlib import Path


# ============================================================================
# DATA MODELS
# ============================================================================

class ShapiroResult(NamedTuple):
    """Result of a Shapiro-Wilk normality test."""
    statistic: float
    p_value: float
    is_normal: bool


class TTestResult(NamedTuple):
    """Result of an independent samples t-test."""
    t_statistic: float
    p_value: float


class WilcoxonResult(NamedTuple):
    """Result of a Wilcoxon rank-sum (Mann-Whitney U) test."""
    statistic: float
    p_value: float


class AnalysisResult:
    """Complete result of the statistical analysis pipeline.
    
    Attributes
    ----------
    shapiro_hospital_1 : ShapiroResult
        Shapiro-Wilk test result for hospital 1.
    shapiro_hospital_2 : ShapiroResult
        Shapiro-Wilk test result for hospital 2.
    test_type : str
        Type of comparison test performed ('t-test' or 'wilcoxon').
    test_result : TTestResult or WilcoxonResult
        Result of the comparison test.
    expanded_size_1 : int
        Size of expanded hospital 1 dataset.
    expanded_size_2 : int
        Size of expanded hospital 2 dataset.
    timestamp : datetime
        When the analysis was performed.
    """
    
    def __init__(
        self,
        shapiro_hospital_1: ShapiroResult,
        shapiro_hospital_2: ShapiroResult,
        test_type: Literal['t-test', 'wilcoxon'],
        test_result: TTestResult | WilcoxonResult,
        expanded_size_1: int,
        expanded_size_2: int
    ):
        self.shapiro_hospital_1 = shapiro_hospital_1
        self.shapiro_hospital_2 = shapiro_hospital_2
        self.test_type = test_type
        self.test_result = test_result
        self.expanded_size_1 = expanded_size_1
        self.expanded_size_2 = expanded_size_2
        self.timestamp = datetime.now()
    
    def is_significant(self, alpha: float = 0.05) -> bool:
        """Check if the comparison test shows a significant difference.
        
        Parameters
        ----------
        alpha : float, default=0.05
            Significance level.
            
        Returns
        -------
        bool
            True if p-value < alpha (significant difference).
        """
        return self.test_result.p_value < alpha
    
    def get_summary(self) -> str:
        """Get a formatted text summary of the analysis.
        
        Returns
        -------
        str
            Formatted summary of all test results.
        """
        lines = []
        lines.append("=" * 70)
        lines.append("HOSPITAL STATISTICAL ANALYSIS RESULTS")
        lines.append("=" * 70)
        lines.append(f"\nAnalysis Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\nDataset Sizes:")
        lines.append(f"  Hospital 1: {self.expanded_size_1} observations")
        lines.append(f"  Hospital 2: {self.expanded_size_2} observations")
        
        lines.append("\n1. SHAPIRO-WILK NORMALITY TESTS")
        lines.append("-" * 70)
        lines.append(f"Hospital 1:")
        lines.append(f"  Statistic (W): {self.shapiro_hospital_1.statistic:.6f}")
        lines.append(f"  P-value:       {self.shapiro_hospital_1.p_value:.6f}")
        lines.append(f"  Normal:        {self.shapiro_hospital_1.is_normal}")
        
        lines.append(f"\nHospital 2:")
        lines.append(f"  Statistic (W): {self.shapiro_hospital_2.statistic:.6f}")
        lines.append(f"  P-value:       {self.shapiro_hospital_2.p_value:.6f}")
        lines.append(f"  Normal:        {self.shapiro_hospital_2.is_normal}")
        
        lines.append(f"\n2. COMPARISON TEST: {self.test_type.upper()}")
        lines.append("-" * 70)
        
        if self.test_type == 't-test':
            lines.append(f"  T-statistic:   {self.test_result.t_statistic:.6f}")
            lines.append(f"  P-value:       {self.test_result.p_value:.6f}")
        else:
            lines.append(f"  U-statistic:   {self.test_result.statistic:.6f}")
            lines.append(f"  P-value:       {self.test_result.p_value:.6f}")
        
        lines.append("\n3. INTERPRETATION")
        lines.append("-" * 70)
        if self.is_significant():
            lines.append(f"  Result: SIGNIFICANT difference (p < 0.05)")
            lines.append("  The two hospitals show statistically different door-to-needle times.")
        else:
            lines.append(f"  Result: NO significant difference (p >= 0.05)")
            lines.append("  The two hospitals show similar door-to-needle times.")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert result to a dictionary for easy integration.
        
        Returns
        -------
        dict
            Dictionary containing all analysis results.
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'dataset_sizes': {
                'hospital_1': self.expanded_size_1,
                'hospital_2': self.expanded_size_2
            },
            'shapiro_wilk': {
                'hospital_1': {
                    'statistic': self.shapiro_hospital_1.statistic,
                    'p_value': self.shapiro_hospital_1.p_value,
                    'is_normal': self.shapiro_hospital_1.is_normal
                },
                'hospital_2': {
                    'statistic': self.shapiro_hospital_2.statistic,
                    'p_value': self.shapiro_hospital_2.p_value,
                    'is_normal': self.shapiro_hospital_2.is_normal
                }
            },
            'comparison_test': {
                'test_type': self.test_type,
                'statistic': (
                    self.test_result.t_statistic if self.test_type == 't-test'
                    else self.test_result.statistic
                ),
                'p_value': self.test_result.p_value,
                'is_significant': self.is_significant()
            }
        }


# ============================================================================
# MAIN ANALYSIS CLASS
# ============================================================================

class HospitalStatistics:
    """Main class for hospital statistical analysis.
    
    This class provides all functionality needed to:
    - Generate synthetic hospital datasets
    - Expand frequency-based datasets
    - Perform normality tests (Shapiro-Wilk)
    - Perform comparison tests (t-test or Wilcoxon)
    - Generate and save results
    
    Parameters
    ----------
    alpha : float, default=0.05
        Significance level for statistical tests.
    
    Examples
    --------
    >>> stats = HospitalStatistics()
    >>> result = stats.run_analysis(n_rows=50, random_state=42)
    >>> print(result.get_summary())
    >>> print(f"Significant: {result.is_significant()}")
    """
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
    
    # ========================================================================
    # DATA GENERATION
    # ========================================================================
    
    @staticmethod
    def generate_dataset(
        n_rows: int = 50,
        door_to_needle_min: int = 30,
        door_to_needle_max: int = 120,
        n_min: int = 1,
        n_max: int = 50,
        random_state: Optional[int] = None
    ) -> pd.DataFrame:
        """Generate a synthetic hospital dataset.
        
        Parameters
        ----------
        n_rows : int, default=50
            Number of rows in the dataset.
        door_to_needle_min : int, default=30
            Minimum door-to-needle time value.
        door_to_needle_max : int, default=120
            Maximum door-to-needle time value.
        n_min : int, default=1
            Minimum frequency value.
        n_max : int, default=50
            Maximum frequency value.
        random_state : int, optional
            Random seed for reproducibility.
            
        Returns
        -------
        pd.DataFrame
            DataFrame with 'door_to_needle' and 'n' columns.
        """
        if random_state is not None:
            np.random.seed(random_state)
        
        door_to_needle = np.random.randint(
            door_to_needle_min, 
            door_to_needle_max + 1, 
            size=n_rows
        )
        
        n = np.random.randint(n_min, n_max + 1, size=n_rows)
        
        return pd.DataFrame({
            'door_to_needle': door_to_needle,
            'n': n
        })
    
    # ========================================================================
    # DATA PROCESSING
    # ========================================================================
    
    @staticmethod
    def expand_dataset(df: pd.DataFrame) -> np.ndarray:
        """Expand a frequency-based dataset.
        
        Takes a DataFrame with 'door_to_needle' and 'n' columns, and expands
        it by repeating each door_to_needle value n times.
        
        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame with 'door_to_needle' and 'n' columns.
            
        Returns
        -------
        np.ndarray
            1D array of expanded values.
            
        Raises
        ------
        ValueError
            If required columns are missing.
        """
        required_columns = {'door_to_needle', 'n'}
        if not required_columns.issubset(df.columns):
            raise ValueError(
                f"DataFrame must contain columns: {required_columns}"
            )
        
        expanded_data = []
        for _, row in df.iterrows():
            expanded_data.extend([row['door_to_needle']] * row['n'])
        
        return np.array(expanded_data, dtype=np.int64)
    
    # ========================================================================
    # STATISTICAL TESTS
    # ========================================================================
    
    def shapiro_wilk_test(self, data: np.ndarray) -> ShapiroResult:
        """Perform Shapiro-Wilk test for normality.
        
        Parameters
        ----------
        data : np.ndarray
            Sample data to test.
            
        Returns
        -------
        ShapiroResult
            Test results including normality decision.
        """
        statistic, p_value = stats.shapiro(data)
        is_normal = p_value > self.alpha
        
        return ShapiroResult(
            statistic=float(statistic),
            p_value=float(p_value),
            is_normal=bool(is_normal)
        )
    
    @staticmethod
    def t_test(data1: np.ndarray, data2: np.ndarray) -> TTestResult:
        """Perform independent samples t-test.
        
        Parameters
        ----------
        data1 : np.ndarray
            First sample.
        data2 : np.ndarray
            Second sample.
            
        Returns
        -------
        TTestResult
            Test results.
        """
        statistic, p_value = stats.ttest_ind(data1, data2)
        
        return TTestResult(
            t_statistic=float(statistic),
            p_value=float(p_value)
        )
    
    @staticmethod
    def wilcoxon_test(data1: np.ndarray, data2: np.ndarray) -> WilcoxonResult:
        """Perform Wilcoxon rank-sum test (Mann-Whitney U).
        
        Parameters
        ----------
        data1 : np.ndarray
            First sample.
        data2 : np.ndarray
            Second sample.
            
        Returns
        -------
        WilcoxonResult
            Test results.
        """
        statistic, p_value = stats.mannwhitneyu(
            data1, data2, alternative='two-sided'
        )
        
        return WilcoxonResult(
            statistic=float(statistic),
            p_value=float(p_value)
        )
    
    # ========================================================================
    # MAIN PIPELINE
    # ========================================================================
    
    def run_analysis_from_arrays(
        self,
        data1: np.ndarray,
        data2: np.ndarray
    ) -> AnalysisResult:
        """Run complete statistical pipeline on two expanded datasets.
        
        Parameters
        ----------
        data1 : np.ndarray
            Expanded data from hospital 1.
        data2 : np.ndarray
            Expanded data from hospital 2.
            
        Returns
        -------
        AnalysisResult
            Complete analysis results.

        Notes
        -----
        Automatically performs:
        1. Shapiro-Wilk normality tests on both datasets
        2. Selection of appropriate comparison test
        3. Execution of comparison test (t-test or Wilcoxon)
        """
        shapiro_1 = self.shapiro_wilk_test(data1)
        shapiro_2 = self.shapiro_wilk_test(data2)
        
        if shapiro_1.is_normal and shapiro_2.is_normal:
            test_type: Literal['t-test', 'wilcoxon'] = 't-test'
            test_result = self.t_test(data1, data2)
        else:
            test_type: Literal['t-test', 'wilcoxon'] = 'wilcoxon'
            test_result = self.wilcoxon_test(data1, data2)
        
        return AnalysisResult(
            shapiro_hospital_1=shapiro_1,
            shapiro_hospital_2=shapiro_2,
            test_type=test_type,
            test_result=test_result,
            expanded_size_1=len(data1),
            expanded_size_2=len(data2)
        )
    
    def run_analysis_from_dataframes(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame
    ) -> AnalysisResult:
        """Run analysis on two frequency-based DataFrames.
        
        Parameters
        ----------
        df1 : pd.DataFrame
            Hospital 1 data with 'door_to_needle' and 'n' columns.
        df2 : pd.DataFrame
            Hospital 2 data with 'door_to_needle' and 'n' columns.
            
        Returns
        -------
        AnalysisResult
            Complete analysis results.
        """
        expanded_1 = self.expand_dataset(df1)
        expanded_2 = self.expand_dataset(df2)
        
        return self.run_analysis_from_arrays(expanded_1, expanded_2)
    
    def run_analysis(
        self,
        n_rows: int = 50,
        random_state: Optional[int] = None,
        **kwargs
    ) -> AnalysisResult:
        """Generate synthetic data and run complete analysis.
        
        Parameters
        ----------
        n_rows : int, default=50
            Number of rows in each dataset.
        random_state : int, optional
            Random seed for reproducibility.
        **kwargs
            Additional parameters for dataset generation
            (door_to_needle_min, door_to_needle_max, n_min, n_max).
            
        Returns
        -------
        AnalysisResult
            Complete analysis results.
        """
        # Generate datasets
        df1 = self.generate_dataset(
            n_rows=n_rows,
            random_state=random_state,
            **kwargs
        )
        
        random_state_2 = random_state + 1 if random_state is not None else None
        df2 = self.generate_dataset(
            n_rows=n_rows,
            random_state=random_state_2,
            **kwargs
        )
        
        return self.run_analysis_from_dataframes(df1, df2)
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    @staticmethod
    def save_result(
        result: AnalysisResult,
        output_path: Optional[str] = None,
        create_dir: bool = True
    ) -> str:
        """Save analysis result to a text file.
        
        Parameters
        ----------
        result : AnalysisResult
            Result to save.
        output_path : str, optional
            Path to save file. If None, saves to './results/' with timestamp.
        create_dir : bool, default=True
            Create directory if it doesn't exist.
            
        Returns
        -------
        str
            Path to the saved file.
        """
        if output_path is None:
            results_dir = Path("results")
            if create_dir:
                results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_results_{timestamp}.txt"
            output_path = results_dir / filename
        else:
            output_path = Path(output_path)
            if create_dir and output_path.parent:
                output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.get_summary())
        
        return str(output_path)


# ============================================================================
# CONVENIENCE FUNCTIONS (for quick usage)
# ============================================================================

def quick_analysis(
    n_rows: int = 50,
    random_state: Optional[int] = None,
    save: bool = False
) -> AnalysisResult:
    """Quick analysis with synthetic data.
    
    Parameters
    ----------
    n_rows : int, default=50
        Number of rows in each dataset.
    random_state : int, optional
        Random seed.
    save : bool, default=False
        Whether to save results to file.
        
    Returns
    -------
    AnalysisResult
        Analysis results.
    """
    stats = HospitalStatistics()
    result = stats.run_analysis(n_rows=n_rows, random_state=random_state)
    
    if save:
        stats.save_result(result)
    
    return result


def analyze_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    save: bool = False
) -> AnalysisResult:
    """Analyze two hospital DataFrames.
    
    Parameters
    ----------
    df1 : pd.DataFrame
        Hospital 1 data.
    df2 : pd.DataFrame
        Hospital 2 data.
    save : bool, default=False
        Whether to save results to file.
        
    Returns
    -------
    AnalysisResult
        Analysis results.
    """
    stats = HospitalStatistics()
    result = stats.run_analysis_from_dataframes(df1, df2)
    
    if save:
        stats.save_result(result)
    
    return result


# ============================================================================
# MAIN (for standalone execution)
# ============================================================================

def main():
    """Standalone execution example.

    Notes
    -----
    Demonstrates basic usage of the module when run as a script.
    Generates synthetic data, performs analysis, displays results,
    and saves to file.
    """
    print("Running hospital statistical analysis...\n")
    
    stats = HospitalStatistics()
    
    result = stats.run_analysis(n_rows=50, random_state=42)
    
    print(result.get_summary())
    
    output_file = stats.save_result(result)
    print(f"\n\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
