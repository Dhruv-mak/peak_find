"""
Peak Matching and Boundary Detection Script

This script processes mass spectrometry data to match features from a CSV file
with detected peaks in a spectrum, and determines peak boundaries.

Author: Dhruv Makwana
Date: June 17, 2025
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scilslab import LocalSession
import sys
import os
import signal
import atexit

# --- Session and Cleanup Management ---

# Global session variable for proper cleanup
global_session = None


def cleanup_session():
    """Clean up the global session. This function is registered with atexit."""
    global global_session
    if global_session is not None:
        try:
            print("\nCleaning up session...", file=sys.stderr)
            global_session.close()
            global_session = None
            print("Session closed successfully.", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Error during session cleanup: {e}", file=sys.stderr)


def signal_handler(signum, frame):
    """Handle interrupt signals to ensure cleanup is called before exiting."""
    print(
        f"\nReceived signal {signal.Signals(signum).name}. Exiting gracefully.",
        file=sys.stderr,
    )
    # The atexit handler will be called automatically.
    sys.exit(0)


# --- Core Processing Functions ---


def calculate_ppm_error(theoretical_mz, observed_mz):
    """Calculate PPM error between theoretical and observed m/z"""
    return abs(theoretical_mz - observed_mz) / theoretical_mz * 1e6


def find_nearest_peak(target_mz, peak_mz_array, max_ppm_error=50):
    """Find the nearest peak within PPM tolerance"""
    ppm_errors = [calculate_ppm_error(target_mz, peak_mz) for peak_mz in peak_mz_array]
    min_error_idx = np.argmin(ppm_errors)

    if ppm_errors[min_error_idx] <= max_ppm_error:
        return min_error_idx, ppm_errors[min_error_idx]
    else:
        return None, None


def find_peak_boundaries(
    peak_idx,
    mz_array,
    intensity_array,
    left_ppm=35,
    right_ppm=35,
    min_intensity_ratio=0.01,
):
    """
    Find left and right boundaries of a peak using multiple criteria:
    1. PPM distance from peak center
    2. Intensity threshold (relative to peak max)
    3. Local minima detection
    """
    peak_mz = mz_array[peak_idx]
    peak_intensity = intensity_array[peak_idx]

    # Calculate PPM-based boundaries
    left_mz_limit = peak_mz * (1 - left_ppm / 1e6)
    right_mz_limit = peak_mz * (1 + right_ppm / 1e6)

    # Find intensity threshold
    intensity_threshold = peak_intensity * min_intensity_ratio

    # Find left boundary
    left_boundary = 0
    for i in range(peak_idx, -1, -1):
        # Stop if we exceed PPM limit
        if mz_array[i] < left_mz_limit:
            left_boundary = i
            break
        # Stop if intensity drops below threshold
        if intensity_array[i] < intensity_threshold:
            left_boundary = i
            break
        # Stop at local minimum (valley between peaks)
        if i > 0 and i < len(intensity_array) - 1:
            if (
                intensity_array[i] < intensity_array[i - 1]
                and intensity_array[i] < intensity_array[i + 1]
            ):
                left_boundary = i
                break
        left_boundary = i

    # Find right boundary
    right_boundary = len(mz_array) - 1
    for i in range(peak_idx, len(mz_array)):
        # Stop if we exceed PPM limit
        if mz_array[i] > right_mz_limit:
            right_boundary = i
            break
        # Stop if intensity drops below threshold
        if intensity_array[i] < intensity_threshold:
            right_boundary = i
            break
        # Stop at local minimum (valley between peaks)
        if i > 0 and i < len(intensity_array) - 1:
            if (
                intensity_array[i] < intensity_array[i - 1]
                and intensity_array[i] < intensity_array[i + 1]
            ):
                right_boundary = i
                break
        right_boundary = i

    return left_boundary, right_boundary


def process_feature_list_direct_with_boundaries(
    df,
    mz_column,
    full_mz_array,
    full_intensity_array,
    max_ppm_error=200,
    left_ppm=50,
    right_ppm=50,
    min_intensity_ratio=0.01,
):
    """
    Direct approach with boundary detection for each matched feature
    """
    result_df = df.copy()

    # Initialize columns
    result_df["matched_spectrum_mz"] = np.nan
    result_df["matched_spectrum_intensity"] = np.nan
    result_df["ppm_error"] = np.nan
    result_df["left_boundary_mz"] = np.nan
    result_df["right_boundary_mz"] = np.nan
    result_df["left_boundary_intensity"] = np.nan
    result_df["right_boundary_intensity"] = np.nan
    result_df["peak_width_da"] = np.nan
    result_df["peak_width_ppm"] = np.nan

    for idx, row in result_df.iterrows():
        target_mz = row[mz_column]

        # Find closest point in spectrum
        mz_differences = np.abs(full_mz_array - target_mz)
        closest_idx = np.argmin(mz_differences)
        closest_mz = full_mz_array[closest_idx]
        closest_intensity = full_intensity_array[closest_idx]

        # Calculate PPM error
        ppm_error = abs(target_mz - closest_mz) / target_mz * 1e6

        if ppm_error <= max_ppm_error:
            # Store basic match info
            result_df.at[idx, "matched_spectrum_mz"] = closest_mz
            result_df.at[idx, "matched_spectrum_intensity"] = closest_intensity
            result_df.at[idx, "ppm_error"] = ppm_error

            # Find boundaries around this point
            left_boundary_idx, right_boundary_idx = find_peak_boundaries(
                closest_idx,
                full_mz_array,
                full_intensity_array,
                left_ppm,
                right_ppm,
                min_intensity_ratio,
            )

            # Store boundary information
            result_df.at[idx, "left_boundary_mz"] = full_mz_array[left_boundary_idx]
            result_df.at[idx, "right_boundary_mz"] = full_mz_array[right_boundary_idx]
            result_df.at[idx, "left_boundary_intensity"] = full_intensity_array[
                left_boundary_idx
            ]
            result_df.at[idx, "right_boundary_intensity"] = full_intensity_array[
                right_boundary_idx
            ]

            # Calculate peak width
            peak_width_da = (
                full_mz_array[right_boundary_idx] - full_mz_array[left_boundary_idx]
            )
            peak_width_ppm = (peak_width_da / closest_mz) * 1e6

            result_df.at[idx, "peak_width_da"] = peak_width_da
            result_df.at[idx, "peak_width_ppm"] = peak_width_ppm

    return result_df


def load_spectrum_data(session, region_id=None):
    """Load spectrum data from an active SLX session."""
    print("Loading spectrum data from active session...")

    dataset = session.dataset_proxy

    # If no region_id provided, try to get the first available region
    if region_id is None:
        region_tree = dataset.get_region_tree()
        # You may need to adjust this logic based on your specific data structure
        print(
            "No region ID provided. You may need to specify --region-id",
            file=sys.stderr,
        )
        print("Available regions:", file=sys.stderr)
        region_tree.print()
        return None, None

    # Get mean spectrum for the specified region
    mean_spectra = dataset.get_mean_spectrum(
        region_id=region_id, normalization_id="Total Ion Count"
    )
    # mean_spectra = dataset.get_mean_spectrum("Regions", region_id)

    mz = mean_spectra["mz"]
    intensities = mean_spectra["intensities"]

    print(f"Loaded spectrum with {len(mz)} data points")
    print(f"m/z range: {mz.min():.2f} - {mz.max():.2f}")

    return mz, intensities


def create_spectrum_plot(mz, intensities, output_path=None):
    """Create and optionally save spectrum plot"""
    plt.figure(figsize=(12, 6))
    plt.plot(mz, intensities, "b-", linewidth=1, label="Mean Spectrum")
    plt.title("Mass Spectrum", fontsize=14, fontweight="bold")
    plt.xlabel("m/z", fontsize=12)
    plt.ylabel("Intensity", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Spectrum plot saved to: {output_path}")
    else:
        plt.show()


def create_feature_list(session, feature_list_name, processed_df):
    dataset = session.dataset_proxy

    # Check for features with identical boundaries and fix them
    same_boundaries_count = len(processed_df[processed_df['left_boundary_mz'] == processed_df['right_boundary_mz']])
    if same_boundaries_count > 0:
        print(f"Info: Found {same_boundaries_count} features with identical left and right boundaries - fixing automatically")

    # For features with same left and right boundaries, set to mz ± 30 ppm
    same_boundaries_mask = processed_df['left_boundary_mz'] == processed_df['right_boundary_mz']
    processed_df.loc[same_boundaries_mask, 'left_boundary_mz'] = processed_df.loc[same_boundaries_mask, 'm/z'] * (1 - 30 / 1e6)
    processed_df.loc[same_boundaries_mask, 'right_boundary_mz'] = processed_df.loc[same_boundaries_mask, 'm/z'] * (1 + 30 / 1e6)
    
    # Now filter out any remaining invalid boundaries (should be none after the fix above)
    processed_df = processed_df[
        processed_df["left_boundary_mz"] < processed_df["right_boundary_mz"]
    ]
    found_mz_intervals = [
        [left, right]
        for left, right in zip(
            processed_df["left_boundary_mz"], processed_df["right_boundary_mz"]
        )
    ]
    feature_table = dataset.feature_table
    new_feature_list_id = feature_table.create_empty_feature_list(feature_list_name)
    new_mz_features = feature_table.write_mz_features(
        new_feature_list_id,
        found_mz_intervals,
        names=processed_df["Name"].tolist(),
        # names=[
        #     x + "_auto" for x in processed_df["Name"].tolist()
        # ],  # won't be required in the future
    )

    # add old intervals as well with +- 30 ppm, Only for testing purposes
    # old_intervals = [
    #     [mz * (1 - 30 / 1e6), mz * (1 + 30 / 1e6)] for mz in processed_df["m/z"].tolist()
    # ]
    # old_mz_features = feature_table.write_mz_features(
    #     new_feature_list_id,
    #     old_intervals,
    #     names=[
    #         x + "_old" for x in processed_df["Name"].tolist()
    #     ],
    # )

    if len(found_mz_intervals) != len(new_mz_features):
        print(
            f"Warning: Mismatch in number of intervals and features created. "
            f"Expected {len(found_mz_intervals)}, got {len(new_mz_features)}",
            file=sys.stderr,
        )

    print(
        f"Feature list '{feature_list_name}' created with {len(new_mz_features)} features."
    )


def main():
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Match features from CSV with mass spectrum peaks and find boundaries",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Input files
    parser.add_argument(
        "--slx-file",
        "-s",
        required=True,
        help="Path to the SLX file containing spectrum data",
    )
    parser.add_argument(
        "--csv-file",
        "-c",
        required=True,
        help="Path to the CSV file containing features to match",
    )
    parser.add_argument(
        "--region-id", "-r", default="Regions", help="Region ID for spectrum extraction"
    )
    parser.add_argument(
        "--feature-list-name",
        "-f",
        required=True,
        help="Feature list name to create in SCILSLab",
    )

    # CSV parameters
    parser.add_argument(
        "--mz-column",
        "-m",
        default="m/z",
        help="Column name containing m/z values in CSV",
    )
    parser.add_argument(
        "--csv-skiprows",
        type=int,
        default=8,
        help="Number of rows to skip when reading CSV",
    )
    parser.add_argument(
        "--csv-delimiter", default=";", help="Delimiter used in CSV file"
    )

    # Matching parameters
    parser.add_argument(
        "--max-ppm-error",
        type=float,
        default=200.0,
        help="Maximum PPM error for feature matching",
    )
    parser.add_argument(
        "--left-ppm",
        type=float,
        default=50.0,
        help="PPM range for left boundary search",
    )
    parser.add_argument(
        "--right-ppm",
        type=float,
        default=50.0,
        help="PPM range for right boundary search",
    )
    parser.add_argument(
        "--min-intensity-ratio",
        type=float,
        default=0.01,
        help="Minimum intensity ratio for boundary detection",
    )

    # Output parameters
    parser.add_argument(
        "--output",
        "-o",
        default="matched_peaks_with_boundaries.csv",
        help="Output CSV filename",
    )
    parser.add_argument(
        "--plot-spectrum", action="store_true", help="Create and save spectrum plot"
    )
    parser.add_argument(
        "--plot-output", default="spectrum_plot.png", help="Filename for spectrum plot"
    )

    # Processing options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # --- Setup Cleanup Handlers ---
    atexit.register(cleanup_session)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # --- Main Application Logic ---
    global global_session
    try:
        # Validate input files
        if not os.path.exists(args.slx_file):
            print(f"Error: SLX file not found: {args.slx_file}", file=sys.stderr)
            sys.exit(1)

        if not os.path.exists(args.csv_file):
            print(f"Error: CSV file not found: {args.csv_file}", file=sys.stderr)
            sys.exit(1)

        # Start the persistent session
        print(f"Starting persistent session with {args.slx_file}...")
        global_session = LocalSession(filename=args.slx_file)
        print("Session started successfully.")

        # Load spectrum data
        mz, intensities = load_spectrum_data(global_session, args.region_id)
        if mz is None:
            print(
                "Failed to load spectrum data. Please check region ID.", file=sys.stderr
            )
            sys.exit(1)

        # Load CSV data
        if args.verbose:
            print(f"Loading CSV data from {args.csv_file}...")

        df = pd.read_csv(
            args.csv_file, skiprows=args.csv_skiprows, delimiter=args.csv_delimiter
        )

        print(f"Loaded CSV with {len(df)} features")

        # Validate mz column
        if args.mz_column not in df.columns:
            print(f"Error: Column '{args.mz_column}' not found in CSV", file=sys.stderr)
            print(f"Available columns: {df.columns.tolist()}", file=sys.stderr)
            sys.exit(1)

        # Process features
        print("Processing features and finding boundaries...")

        final_results = process_feature_list_direct_with_boundaries(
            df=df,
            mz_column=args.mz_column,
            full_mz_array=mz,
            full_intensity_array=intensities,
            max_ppm_error=args.max_ppm_error,
            left_ppm=args.left_ppm,
            right_ppm=args.right_ppm,
            min_intensity_ratio=args.min_intensity_ratio,
        )

        # Calculate and display results
        matched_count = final_results["matched_spectrum_mz"].notna().sum()
        total_count = len(final_results)
        match_rate = (matched_count / total_count) * 100 if total_count > 0 else 0

        print(f"\n=== RESULTS SUMMARY ===")
        print(f"Total features processed: {total_count}")
        print(f"Successfully matched: {matched_count}")
        print(f"Match rate: {match_rate:.1f}%")

        if matched_count > 0:
            matched_data = final_results[final_results["matched_spectrum_mz"].notna()]
            print(f"\n=== MATCHING STATISTICS ===")
            print(
                f"PPM Error - Mean: {matched_data['ppm_error'].mean():.1f}, Median: {matched_data['ppm_error'].median():.1f}"
            )
            print(
                f"Peak Width (PPM) - Mean: {matched_data['peak_width_ppm'].mean():.1f}, Median: {matched_data['peak_width_ppm'].median():.1f}"
            )
            print(
                f"Peak Width (Da) - Mean: {matched_data['peak_width_da'].mean():.4f}, Median: {matched_data['peak_width_da'].median():.4f}"
            )

        if args.output:
            final_results.to_csv(args.output, index=False)
            print(f"\n✅ Results saved to: {args.output}")

        try:
            create_feature_list(global_session, args.feature_list_name, final_results)
            print(f"Feature list '{args.feature_list_name}' created successfully.")
        except Exception as e:
            print(
                f"Error creating feature list '{args.feature_list_name}': {str(e)}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Create spectrum plot if requested
        if args.plot_spectrum:
            create_spectrum_plot(mz, intensities, args.plot_output)

        print(f"\n🎯 Processing complete!")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
