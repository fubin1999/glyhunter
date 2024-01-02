library(tidyverse)
if (!require("glycanr", quietly = TRUE)) {
  install.packages("glycanr")
}

# Data produced in this script:
# - data1: The raw data in the long format.
# - data2: Data with sample outliers filtered.
# - data3: Data with only glycans with high detection ratio and with 
#          structure information.
# - data4: Data with missing values imputed.
# - data5: Data normalized.
# - data6: Final data in the wide format.

# Read Data---------------------------------------------------------------------
convert_glycan <- function(glycan) {
  longs <- c("Hex", "HexNAc", "dHex", "NeuAc")
  shorts <- c("H", "N", "F", "S")
  patterns <- str_glue("{longs}\\((\\d+)\\)")
  n <- str_match(glycan, patterns)[,2]
  parts <- if_else(
    condition = is.na(n),
    true = "",
    false = str_c(shorts, n)
  )
  str_c(parts, collapse = "")
}

data1 <- read_csv("data/HCC/raw.csv") %>%
  # Convert from Abbr. to short names (e.g. Hex(5)HexNAc(2) to H5N2)
  mutate(
    composition = str_replace(composition, "\\[.*?]", ""),
    composition = map_chr(composition, convert_glycan),
  ) %>%
  rename(glycan = composition) %>%
  # Convert wide data to long data.
  pivot_longer(cols = -glycan, names_to = "sample", values_to = "value")

# Filter Abnormal Samples-------------------------------------------------------
# Detect outliers with the boxplot algorithm.
# Only filter out sample with total area less than Q1 - 1.5 * (Q3 - Q1).
total_intensities <- data1 %>%
  group_by(sample) %>%
  summarise(total = sum(value, na.rm = TRUE))
quantile_25 <- quantile(total_intensities$total) %>%
  quantile(probs = c(0.25), na.rm = TRUE)
quantile_75 <- quantile(total_intensities$total) %>%
  quantile(probs = c(0.75), na.rm = TRUE)
iqr <- quantile_75 - quantile_25
upper <- quantile_75 + 1.5 * iqr
lower <- quantile_25 - 1.5 * iqr
samples_to_keep <- total_intensities %>%
  filter(total > lower) %>%
  pull(sample)
data2 <- data1 %>%
  filter(sample %in% samples_to_keep)

# Filter Glycans----------------------------------------------------------------
glycans_with_high_detect_ratio <- data2 %>%
  group_by(glycan) %>%
  summarise(detect_ratio <- mean(!is.na(value))) %>%
  pull(glycan)

glycans_with_strucutures <- read_csv("data/HCC/serum_structures.csv") %>%
  pull("Composition")

data3 <- data2 %>%
  filter(
    # Keep glycans detected in more than 50% sample.
    glycan %in% glycans_with_high_detect_ratio,
    # Keep glycans with structure information.
    glycan %in% glycans_with_strucutures
  )

# Fill Missing Values-----------------------------------------------------------
# Fill missing values with half the lowest abundance of a glycan.
data4 <- data3 %>%
  group_by(glycan) %>%
  mutate(
    min = min(value, na.rm = TRUE),
    value = if_else(is.na(value), min / 2, value)
  ) %>%
  select(-min)

# Normalization-----------------------------------------------------------------
data5 <- data4 %>%
  # Prepare the data for using the `glycanr` package
  rename(gid = sample) %>%
  glycanr::tanorm() %>%
  glycanr::medianquotientnorm() %>%
  rename(sample = gid)

# Set groups--------------------------------------------------------------------
# groups <- read_csv("data/HCC/raw_groups.csv")
# groups_filtered <- groups %>%
#   filter(type != "Y") %>%
#   mutate(group = if_else(type == "C", "T", "C")) %>%
#   select(-type)
# data6 = groups_filtered %>%
#   left_join(data5, by = "sample")

# Prepare clinical information--------------------------------------------------
# raw_cli <- read_csv("data/HCC/raw_clinical_information.csv")
# 
# cli <- groups_filtered %>%
#   left_join(raw_cli, by = join_by(raw_name == No)) %>%
#   select(-raw_name)

# Convert to wide format--------------------------------------------------------
data6 <- data5 %>%
  pivot_wider(id_cols = sample, names_from = glycan, values_from = value)

# Save Results------------------------------------------------------------------
write_csv(data6, "data/HCC/glycans_prepared.csv")
# write_csv(groups_filtered, "data/HCC/groups.csv")
# write_csv(cli, "data/HCC/clinical_information.csv")
