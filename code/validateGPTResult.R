# this script is for checking performance of gpt results

pkgs <- c('dplyr', 'tidyr', 'readxl', 'writexl', 'caret')
lapply(pkgs, library, character.only=TRUE)

df <- read.csv('output/gpt_analysis_results.csv')
df <- df %>% 
  mutate(shortid=ifelse(startsWith(File_Name, "J"), 
                        substr(File_Name,1,5), substr(File_Name, 1, 3)),
         shortid=gsub(" ", "", shortid))

# clean up codebook id
codebook <- read_excel('lit/AllJan25/merged_lit_100rand_val_codebook_2501.xlsx')
str(codebook)
codebook <- codebook %>% mutate(
  ID=ifelse((nchar(ID)==2) & (!startsWith(ID, "C")), paste0("0", ID), ID)
)

# merge two tabs
all <- merge(df, codebook, by.x="shortid", by.y='ID')
# remove two problematic ones
all <- all %>% filter(!shortid %in% c("J1786", "J5677"))
# compare countries
country <- all %>% select(shortid, Study_Country, country)
# compare habitat types
hab <- all %>% select(shortid, Habitat_Types, habitat_type)
# compare spatial scale
scale <- all %>% select(shortid, Spatial_Scale, spatial_scale)

# compare topics
topics_struc <- all %>% select(shortid, structure_3d, Structure_vertical_3d, Structure_vertical_3d_Confidence, structure_2d, Structure_horizontal_2d, Structure_horizontal_2d_Confidence)

topics_bio <- all %>% select(shortid, animal_3d, Animal_vertical_3d, Animal_vertical_3d_Confidence, animal_2d, Animal_horizontal_2d, Animal_horizontal_2d_Confidence)

topics_cor <- all %>% select(shortid, correlation, Relationship_Structure.Animal.Correlation, Relationship_Structure.Animal.Correlation_Confidence)

topics_struc_on_an <- all %>% select(shortid, structure_on_animal, Relationship_Effect.Structure.On.Animals, Relationship_Effect.Structure.On.Animals_Confidence)

topics_an_on_struc <- all %>% select(shortid, animal_on_structure, Relationship_Effect.Animals.On.Structure, Relationship_Effect.Animals.On.Structure_Confidence)

# compare airborne lidar
als <- all %>% select(shortid, airborne_lidar, Method_Airborne.Lidar_Regex,
                      Method_Airborne.Lidar_GPT, Method_Airborne.Lidar_Evidence)

tls <- all %>% select(shortid, terr_lidar, Method_Terrestrial.Lidar_Regex,
                      Method_Terrestrial.Lidar_GPT, Method_Terrestrial.Lidar_Evidence)

spc <- all %>% select(shortid, spaceborne_lidar, Method_Spaceborne.Lidar_Regex,
                      Method_Spaceborne.Lidar_GPT, Method_Spaceborne.Lidar_Evidence)

fieldsamp <- all %>% select(shortid, field_sampling, 
                      Method_Field.Sampling_GPT, Method_Field.Sampling_Regex,
                      Method_Field.Sampling_Evidence)
otherrs <- all %>% select(shortid, other_rs, Method_Other.Remote.Sensing_GPT,
                          Method_Other.Remote.Sensing_Regex, Method_Other.Remote.Sensing_Evidence)

# compare metrics
cover <- all %>% select(shortid, cover, Metric_Cover.Density_Present, Metric_Cover.Density_Regex, Metric_Cover.Density_Used)

height <- all %>% select(shortid, height, Metric_Height_Present, Metric_Height_Regex, Metric_Height_Evidence)

hor_het <- all %>% select(shortid, horizontal_het, Metric_Horizontal.Heterogeneity_Present, Metric_Horizontal.Heterogeneity_Regex, Metric_Horizontal.Heterogeneity_Evidence)

ver_het <- all %>% select(shortid, vertical_het, Metric_Vertical.Heterogeneity_Present, Metric_Vertical.Heterogeneity_Regex, Metric_Vertical.Heterogeneity_Evidence)

# compare taxa
taxa <- all %>% select(shortid, taxa, Animal_Taxa_Studied)

# compare sampling method
smpl_method <- all %>% select(shortid, sampling_method, Animal_Sampling_Methods)

# compare tasks
sr <- all %>% select(shortid, species_richness, Animal_Species.Richness_Present,
                     Animal_Species.Richness_Regex, Animal_Species.Richness_Metrics,
                     Animal_Species.Richness_Evidence)


# ======== append abstract info to merged_lit =======
merged_lit <- read_excel('lit/AllJan25/merged_lit_2501.xlsx')
rawinfo <- read_excel('lit/Boosted lit search/Jan2025/newfiles5.xlsx') %>% select(`Article Title`, Abstract, `Publication Year`)

merged_lit <- merge(merged_lit, rawinfo, by.x='Title', by.y='Article Title', all.x=TRUE)

write_xlsx(merged_lit, 'lit/AllJan25/merged_lit_2501_withabstract.xlsx')
