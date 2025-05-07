# this script is for post process gpt results and filter down papers

pkgs <- c('dplyr', 'tidyr', 'readxl', 'writexl', 'caret')
lapply(pkgs, library, character.only=TRUE)

gpt <- read.csv('output/gpt_analysis_results.csv')

df_col_name <- colnames(gpt)
regex_names <- df_col_name[endsWith(df_col_name, "_Regex")]
evidence_names <- df_col_name[endsWith(df_col_name, "_Evidence")]

# drop regex results right now
gpt <- gpt %>% select(!any_of(regex_names)) %>% select(!any_of(evidence_names))
gpt <- gpt %>% mutate(
  ID = gsub(".pdf", "", gpt$File_Name),
  ID = substr(ID, 1, 5),
  ID = sub(" .*", "", ID))


lit_info <- read_excel('lit/AllJan25/merged_lit_2501_withabstract.xlsx') %>% select('Title', 'ID', 'Publication Year', 'Abstract')
gpt <- merge(gpt, lit_info, by='ID', all.x=TRUE)

# get a subset that meets the basic criteria
# note that this is removing purely structural connectivity studies
kept1 <- gpt %>% filter(Method_Spaceborne.Lidar_GPT=="True" | Method_Airborne.Lidar_GPT=="True" | Method_Terrestrial.Lidar_GPT=="True" | Method_Structure.From.Motion_GPT=="True" | Vertical_Layer=="True" | Animal_Acoustic.Monitoring_Present=="True" | Animal_Vertical.Movement_Present=="True"|(Metric_Cover.Density_Present=="True" & (Metric_Height_Present=="True"|Metric_Vertical.Heterogeneity_Present=="True"))|grepl("vertical", Animal_Major.Tasks_Metrics))

removed <- gpt %>% filter(!(Method_Spaceborne.Lidar_GPT=="True" | Method_Airborne.Lidar_GPT=="True" | Method_Terrestrial.Lidar_GPT=="True" | Method_Structure.From.Motion_GPT=="True" | Vertical_Layer=="True" | Animal_Acoustic.Monitoring_Present=="True" | Animal_Vertical.Movement_Present=="True"|(Metric_Cover.Density_Present=="True" & (Metric_Height_Present=="True"|Metric_Vertical.Heterogeneity_Present=="True"))|grepl("vertical", Animal_Major.Tasks_Metrics)))


# further remove papers
# remove those without any spatial info or country info
kept2 <- kept1 %>% filter(!(Study_Country=="text" & Spatial_Extent=="text" & Habitat_Types=="text")) %>% filter(Study_Country!="text") # 16 removed

# remove those with coastal, floodplain, or meadow, or open water, or tidal
kept3 <- kept2 %>% filter(!grepl("coastal|floodplain|meadow|water|mangrove|tidal", Habitat_Types))

# remove those that don't have a target species or a animal related task
kept4 <- kept3 %>% filter(Animal_Taxa_Studied!="" & Animal_Major.Tasks_Present!="False") # removed 12

# check if height measures are correct
unique(kept2$Metric_Height_Used)

kept4 <- kept4 %>% 
  mutate(safe = ifelse(Method_Spaceborne.Lidar_GPT=="True" | Method_Airborne.Lidar_GPT=="True" | Method_Terrestrial.Lidar_GPT=="True" | Method_Structure.From.Motion_GPT=="True" | Vertical_Layer=="True" | Animal_Acoustic.Monitoring_Present=="True" | Animal_Vertical.Movement_Present=="True", 1, 0))




kept4 <- kept4 %>%
  mutate(if3dStruc = ifelse(Metric_Height_Present=="True" | Metric_Vertical.Heterogeneity_Present=="True", 1, 0),
         if3dAnim = ifelse(Animal_Acoustic.Monitoring_Present=="True"|Animal_Vertical.Movement_Present=="True"|grepl("vertical", Animal_Major.Tasks_Metrics), 1, 0))

write_xlsx(kept4, 'output/gpt_results_kept4.xlsx')

# J1134, J0579 are duplicated so remove
kept4 <- kept4 %>% filter(!ID %in% c("J1134", "J0579"))
tmp <- kept4 %>% filter(grepl("connectivity", Title))

colnames(kept4)

# remove J0326 for studying stored maize depth
# manually removed J1528, J5677, J1052, J2927 because of duplication
# manually removed J1967 because it doesn't measure habitat structure or animals in 3d
# manually removed J1993 because it is about classifying species in audio recordings
# manually removed J3251 because it is not using vertical layers or other 3d stuff
# manually removed J3313, J3431, J4605, J5848, J5678, 488, J0359, J1071, J4743, J4111, J5978, J0717, J0568, J2528 because they are not using 3d stuff
# manually removed J3651 because it is a review
# manually removed J3954 because it is a commentary
# manually removed J4206 because it is about faunal communities (no animals)
# manually removed J4409 because it is a recommendation, no analysis
# manually removed J4570, J3736 because they are just using elevation as 3d
# manually removed J4701 because it is a meta analysis and does not measure 3d explicitly
# manually removed J4978 because it is about dwelling underground
# manually removed J5500 because it is not that 3d
# manually removed 016, 295 because they are not about animals
# manually removed J0326 because it is about maize depth

# not removed but hallucinating...
# J2067


# ============ merge field sampling evidence with codebook ==========
codebook <- read_excel('output/gpt_results_kept4_codebook.xlsx')

df_year <- codebook[!is.na(codebook$`Publication Year`),]
hist(df_year$`Publication Year`)
df_year$five_year <- round(df_year/5)

df0 <- read_excel('data/lit_coding_0828.xlsx')
colnames(df0) <- df0[1,]
df0 <- df0[-c(1), ]

df <- df0 %>% select(ID, `Publication Year`) %>% mutate(
  nchars = nchar(ID),
  ID = ifelse(nchars==1, paste0("00", ID), ifelse(nchars==2, paste0("0", ID), ID))
)
colnames(df) <- c('ID', 'pub year')

codebook1 <- merge(codebook, df, by='ID', all.x=TRUE)
codebook1 <- codebook1 %>% mutate(
  year = ifelse(!is.na(`Publication Year`), `Publication Year`, ifelse(
    !is.na(`pub year`),  `pub year`, 0
  )),
  `if3dStruc` = ifelse(is.na(`if3dStruc`), 0, `if3dStruc`)
)

codebook1$year <- as.numeric(codebook1$year)

hist(codebook1$year)

unique(codebook1$if3dStruc)

df_3dstruc <- codebook1[codebook1$if3dStruc==1,]

hist(df_3dstruc$year)

df_3dstruc$year_5 <- 5*ceiling(df_3dstruc$year/5)
hist(df_3dstruc$year_5)

a <- as.data.frame(table(df_3dstruc$year))

ggplot(a, aes(x=Var1, y=Freq))+
  geom_point()
