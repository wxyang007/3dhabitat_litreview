pkgs <- c('dplyr', 'tidyr', 'readxl', 'writexl', 'caret')
lapply(pkgs, library, character.only=TRUE)

getwd()

rawfiles <- list.files('boosted lit search/Jan2025', pattern="\\.xls$")
newfiles <- data.frame()
for(i in 1:length(rawfiles)){
  df_i <- read_excel(file.path('boosted lit search/Jan2025', rawfiles[i]))
  newfiles <- rbind(newfiles, df_i)
}

oldfile0 <- read.csv('lit_search_0514.csv') %>% select('Title') %>% rename('Article Title' = 'Title')
oldfile1 <- read.csv('Boosted lit search/conservation/conservation_edt1_Aug28_2024.csv') %>% select('Article Title'='Article.Title')
oldfile2 <- read.csv('Boosted lit search/vegetation structure/veg_structure_edt2_Aug26_2024.csv') %>% select('Article Title'='Article.Title')

oldfiles <- rbind(oldfile0, oldfile1, oldfile2) %>% distinct(`Article Title`)
oldfiles$ifExist <- 1

df <- merge(newfiles, oldfiles, by=c("Article Title"), all.x=TRUE) %>% mutate(ifExist=replace_na(ifExist, 0))

df_remain <- df %>% filter(ifExist==0)

write_xlsx(df_remain, 'Boosted lit search/Jan2025/newfiles.xlsx')

# ============================== make bulk edits ===============================

newfile <- read_excel('lit/Boosted lit search/Jan2025/newfiles5.xlsx')

nrow(newfile %>% filter(ifKeep==0))
nrow(newfile)-nrow(newfile %>% filter(ifKeep==0))
newfile <- newfile %>% 
  mutate(
    # Special groups that need extra attention
    # underpasses or overpasses
    ifPass = ifelse(grepl("overpass|underpass|Overpass|Underpass|crossing", `Article Title`), 1, 0),
    # bridges - canopy bridges or road bridges
    ifBridge = ifelse(grepl("bridge|Bridge", `Article Title`), 1, 0),
    # ecosystem engineer
    ifEng = ifelse(grepl("engineer|Engineer", `Article Title`), 1, 0),
    
    # Groups to remove
    ifCoast = ifelse(grepl("coast |Coast |coastal|Coastal|mussel|Mussel|sea |Sea |bathymet|Bathymet", `Article Title`), 1, 0),
    ifCoast = ifelse(grepl("coast |Coast |coastal|Coastal|mussel|Mussel|sea |Sea |bathymet|Bathymet", `Abstract`), 1, ifCoast),
    ifRiver = ifelse(grepl(" river|River|riparian|Riparian|wetland|Wetland|mangrove|Mangrove| lake|Lake ", `Article Title`), 1, 0),
    ifCavity = ifelse(grepl("cavity", `Article Title`), 1, 0),
    ifHeight = ifelse(grepl("height estimat|Height Estimat", `Article Title`), 1, 0),
    ifBacteria = ifelse(grepl("bacteria|Bacteria|microb|Microb", `Article Title`), 1, 0),
    ifBacteria = ifelse(grepl("bacteria|Bacteria|microb|Microb", `Abstract`), 1, 0),
    ifKarst = ifelse(grepl("karst |Karst ", `Article Title`), 1, 0),
    ifKarst = ifelse(grepl("karst |Karst ", `Abstract`), 1, 0),
    
    # Groups that likely keep
    ifStruc = ifelse(grepl("structur|3d|3D|three dimension|vertical", `Abstract`), 1, 0))

# newfile <- newfile %>% mutate(ifKeep = ifelse(ifCoast+ifRiver+ifCavity+ifHeight>0, 0, ifKeep))
newfile <- newfile %>% mutate(ifKeep = ifelse(ifKarst>0, 0, ifKeep))
bridgeNPass <- newfile %>% filter(ifBridge+ifPass>0 & ifCoast+ifRiver+ifCavity+ifHeight == 0)
ecoEng <- newfile %>% filter(ifEng>0  & ifCoast+ifRiver+ifCavity+ifHeight == 0)


write_xlsx(newfile, 'lit/Boosted lit search/Jan2025/newfiles5.xlsx')

text = 'Canopy openness as the main driver of aculeate Hymenoptera and saproxylic beetle diversity following natural disturbances and salvage logging'
grepl(" river", text)


# ============================== clean gpt outputs ===============================
df <- read_excel('lit/Boosted lit search/Jan2025/newfiles5_pred_predictions.xlsx')
df <- df[!duplicated(df), ]
write_xlsx(df, 'lit/Boosted lit search/Jan2025/newfiles5_pred_predictions_unq.xlsx')
nrow(df[df$Prediction=='keep',]) # 1,514
nrow(df[df$Prediction=='remove',]) # 1,514

kept <- df %>% filter(Prediction == "keep") %>%
  mutate(    # underpasses or overpasses
    ifPass = ifelse(grepl("overpass|underpass|Overpass|Underpass|crossing", `Title`), 1, 0),
    # bridges - canopy bridges or road bridges
    ifBridge = ifelse(grepl("bridge|Bridge", `Title`), 1, 0),
    # ecosystem engineer
    ifEng = ifelse(grepl("engineer|Engineer", `Title`), 1, 0),)
bridgeNPass_kpt <- kept %>% filter(ifBridge+ifPass>0)
ecoEng_kpt <- kept %>% filter(ifEng>0)





set.seed(226)

# Randomly select 100 rows for each group (e.g., ifKeep = 0 and ifKeep = 1)
sample_size <- 100
sampled_df <- rbind(
  df %>% filter(Prediction == "keep") %>% slice_sample(n = sample_size),
  df %>% filter(Prediction == "remove") %>% slice_sample(n = sample_size)
)


df_full <- read_excel('lit/Boosted lit search/Jan2025/newfiles5_pred.xlsx')
sampled_df <- merge(sampled_df, df_full, by.x="Title", by.y="Article Title", all.x=TRUE)
write_xlsx(sampled_df, 'lit/Boosted lit search/Jan2025/newfiles5_pred_sampled_val.xlsx')


sampled_df <- read_excel('lit/Boosted lit search/Jan2025/newfiles5_pred_sampled_val.xlsx')
detailed_metrics <- confusionMatrix(
  factor(sampled_df$Prediction, levels = c("keep", "remove")),
  factor(sampled_df$ifKeep, levels = c("keep", "remove"))
)

# This will show accuracy, sensitivity, specificity, etc.
print(detailed_metrics)
