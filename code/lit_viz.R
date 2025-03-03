# Process literature
# script originally built for generating figures for landscape sustainability final term paper
# author: Wenxin Yang
# date: 11.23.2023
# version: 01/07/2025
# version: 02/10/2025
# version: 03/03/2025

pkgs <- c('plyr', 'tidyverse', 'sf', 'biscale', 'hrbrthemes', 'dplyr', 'tidyr',
          'networkD3', 'RColorBrewer', 'VennDiagram', 'cowplot', 'stringr', 'readxl',
          'viridis', 'janitor', 'data.table', 'ggrepel', 'tmap', 'skimr')

lapply(pkgs, library, character.only=TRUE)

getwd()

# ====== preprocessing steps ======
# read the focused search results
df00 <- read_excel('data/lit_coding_241230.xlsx', sheet='Journal articles')
colnames(df00) <- df00[1,]

df01 <- df00 %>% select(ID, `Publication Year`) %>% mutate(
  nchars = nchar(ID),
  ID = ifelse(nchars==1, paste0("00", ID), ifelse(nchars==2, paste0("0", ID), ID))
)
colnames(df01) <- c('ID', 'pub year')

# read the expansive search results
df0 <- read_excel('output/gpt_results_kept4_codebook_Feb.xlsx')

# get pub year info
df <- merge(df0, df01, by='ID', all.x=TRUE)
# remove column with names of NA
df <- df[!is.na(names(df))]

df <- df %>% mutate(
  year = ifelse(!is.na(`Publication Year`), `Publication Year`, ifelse(
    !is.na(`pub year`),  `pub year`, 0
  )),
  `if3dStruc` = ifelse(is.na(`if3dStruc`), 0, `if3dStruc`),
  `if3dAnim` = ifelse(is.na(`if3dAnim`), 0, `if3dAnim`),
  `ifCor` = ifelse(is.na(`ifCor`), 0, `ifCor`),
  `ifStrucAni` = ifelse(is.na(`ifStrucAni`), 0, `ifStrucAni`),
  `ifAniStruc` = ifelse(is.na(`ifAniStruc`), 0, `ifAniStruc`)
)

df$year <- as.numeric(df$year)
df <- df[!is.na(names(df))]
df <- df %>% select(-c('comments', 'Abstract', 'Publication Year', 'pub year'))

# ===========================================================================
# ===== [version 2024] change variable type to numeric =====
# topical cols
# top_cols <- c('Habitat', 'Biodiversity', 'Correlate', 'Cause', 'Affected','Exogenous')
# habitat data cols
# hab_dat_cols <- c('Field veg data', 'Terrestrial LiDAR', 'Drone LiDAR', 'Airborne LiDAR', 'Other LiDAR', 'Spaceborne LiDAR', 'UAV SAR', 'airplane/drone optical', 'Optical', 'Other hab data')
# habitat metrics cols
# hab_met_cols <- c('Cover', 'Height', 'Horizontal var.', 'Vertical var.')
# biodiversity tasks
# bio_tsk_cols <- c('Species richness', 'Species diversity', 'Functional diversity', 'Species prevalence', 'Species abundance', 'Species absence /presence', 'Speices distribution', 'SDM', 'Habitat occupancy', 'Species survival/mortality', 'Predation rate', 'Movement', 'Habitat suitability', 'Vertical stratification', 'Community similarity/dis-', 'species trait') # other tasks

#for (col in c(top_cols, hab_dat_cols, hab_met_cols, bio_lev_cols, bio_spe_cols, bio_tsk_cols, 'Publication Year')){
#  print(col)
#  df[col] <- as.numeric(df[[col]])
#}
# ===========================================================================

# ====== [version 2025] convert True False to 1,0 ======
hab_dat_cols <- c('Method_Airborne.Lidar_GPT', 'Method_Terrestrial.Lidar_GPT', 'Method_Spaceborne.Lidar_GPT', 'Method_Structure.From.Motion_GPT', 'Method_Field.Sampling_GPT', 'Method_Other.Remote.Sensing_GPT', 'Method_Other.Field_GPT')
hab_met_cols <- c('Metric_Cover.Density_Present', 'Metric_Height_Present', 'Metric_Horizontal.Heterogeneity_Present', 'Metric_Vertical.Heterogeneity_Present', 'Metric_Landscape_Present', 'Metric_Other.Structure_Present')

toBinary <- function(datframe, vars){
  print(vars)
  datframe %>%
    dplyr::mutate(across(all_of(vars), ~ifelse(. == "True", 1, 0)))
}

df1 <- df

df1 <- toBinary(df, c(hab_dat_cols, hab_met_cols))

str(df1)


# biodiversity levels
bio_lev_cols <- c('Individual', 'Population', 'Community', 'Ecosystem/landscape??')
# studied species
bio_spe_cols <- c('Other mammals', 'Bats', 'Birds', 'Primates', 'Reptiles', 'Amphibians', 'Invertebrates', 'Plants') # other species

# replace NA values with 0s for numeric columns
df1 <- df1 %>% mutate_if(is.numeric, ~replace_na(., 0))

# ========== Map ==========
admin <- read_sf('data/worldbound/reproj.shp')

# first clean up country fields
unique(df1$Study_Country)
# replace "and" with ","
# replace ", " with ";"

loc <- df1 %>% select(c("ID", "Study_Country", "if3dStruc", "if3dAnim")) %>% 
  mutate(
    Study_Country = gsub(" and ", ", ", Study_Country)
)

loc <- loc %>% mutate(Study_Country = gsub(", ", ";", Study_Country))
loc <- loc %>% mutate(Study_Country = gsub("/", ";", Study_Country))
unique(loc$Study_Country)


# clean up individual country names
# Global
loc <- loc %>% mutate(Study_Country = gsub("North America;Europe;Asia", "Global", Study_Country))
# NAs
loc <- loc %>% mutate(Study_Country = gsub("not specified|unknown", "Unknown", Study_Country))
# China
loc <- loc %>% mutate(Study_Country = gsub("Taiwan|China|Hong Kong", "People's Republic of China", Study_Country))
# United States of America
loc <- loc %>% mutate(Study_Country = gsub("USA|U.S.A.|United States|Texas;New Jersey;New York|Hawaii", "United States of America", Study_Country))
# United Kingdom
loc <- loc %>% mutate(Study_Country = gsub("UK|England|Scotland|Wales", "United States of America", Study_Country))
# Czech Republic, Netherlands, The Bahamas
loc <- loc %>% mutate(Study_Country = gsub("Czechia", "Czech Republic", Study_Country))
loc <- loc %>% mutate(Study_Country = gsub("The Netherlands", "Netherlands", Study_Country))
loc <- loc %>% mutate(Study_Country = gsub("Bahamas", "The Bahamas", Study_Country))
loc <- loc %>% mutate(Study_Country = gsub("Côte d'Ivoire", "Ivory Coast", Study_Country))

# French Guiana is part of France in the map
loc <- loc %>% mutate(Study_Country = gsub("French Guiana", "France", Study_Country))

clean <-function(col){
  li <- as.list(col)
  li <- li[!is.na(li)]
  str_li <- paste(unlist(li), sep=';', collapse=';')
  
  li1 <- as.list(strsplit(str_li, ';')[[1]])
  df1 <- t(as.data.frame(li1))
  freq <- as.data.frame(table(df1))
  return(freq)
}

freq_loc <- clean(loc$Study_Country)
colnames(freq_loc) <- c('country', 'study_area_cnt')

# now create the map
map_loc <- merge(admin, freq_loc, by.x='NAME_EN', by.y='country'
                 , all.x=TRUE
)
map_loc <- map_loc[c('NAME_EN', 'study_area_cnt')]
colnames(map_loc) <- c('NAME_EN', 'Count', 'geometry')
map_loc[is.na(map_loc)] <- 0

df_map_loc <- map_loc
df_map_loc$geometry <- NULL
# write.csv(df_map_loc, 'location_counts.csv')

# identify missing ones in the first run
li_lit_country <- unique(freq_loc$country)
li_map_country <- unique(map_loc$NAME_EN)

setdiff(li_lit_country, li_map_country)

map_pal <- c('#d3d3d3',"#EDEF5C","#97D267","#47B679","#009780","#00767A","#255668")

freq_map <- tm_shape(map_loc) +
  tm_fill("Count", 
          fill.legend=tm_legend(title='Frequency of study \nareas in each country ', na.show=FALSE, title.fontfamily = 'Times', 
                                # frame=FALSE,
                                title.fontface = 2,
                                text.fontfamily = 'Times', 
                                item_text.margin= 3,
                                labels=c('0', '1 to 4', '5 to 9', '10 to 49', '50 to 110', '326')
                                ),
          fill.scale=tm_scale_intervals(values=map_pal, breaks=c(0,1,5,10,50,110,400), label.na=FALSE)
          )+
  tm_borders(col='black', lwd=0.5)+
  # tm_shape(admin)+
  tm_layout(frame=FALSE)

tmap_save(tm = freq_map, filename = "viz/country_frequency_map_2025.png")


# ========= Bivariate Choropleth Map =======

thedf <- thedf[thedf[colname]==1, ]
newdf <- clean(thedf[areaname])

clean_num <-function(thedf, colname, areaname){
  thedf <- thedf[thedf[colname]==1, ]
  newdf <- clean(thedf[areaname])
  return(newdf)
}

freq_loc_struc <- clean_num(loc, 'if3dStruc', 'Study_Country')
colnames(freq_loc_struc) <- c('country', '3dStruc_cnt')
freq_loc_anim <- clean_num(loc, 'if3dAnim', 'Study_Country')
colnames(freq_loc_anim) <- c('country', '3dAnim_cnt')
freq_loc_bivar <- merge(freq_loc_struc, freq_loc_anim, by='country', all = TRUE)
freq_loc_bivar[is.na(freq_loc_bivar)] <- 0

map_loc_bivar <- merge(admin, freq_loc_bivar, by.x='NAME_EN', by.y='country'
                 , all.x=TRUE
)
map_loc_bivar <- map_loc_bivar[c('NAME_EN', '3dStruc_cnt', '3dAnim_cnt')]
map_loc_bivar[is.na(map_loc_bivar)] <- 0

#df_map_loc_bivar <- map_loc_bivar
#df_map_loc_bivar$geometry <- NULL

#bivar_loc <- bi_class(map_loc_bivar, x='3dStruc_cnt', y='3dAnim_cnt', 
#                      style='equal', 
#                      dim=4)

# customize the classes
map_loc_bivar <- map_loc_bivar %>% mutate(
  class_struc = ifelse(`3dStruc_cnt`>=50, 4, ifelse(`3dStruc_cnt`>=5, 3, ifelse(`3dStruc_cnt`>=1, 2, 1))),
  class_anim = ifelse(`3dAnim_cnt`>=10, 4, ifelse(`3dAnim_cnt`>=3, 3, ifelse(`3dAnim_cnt`>=1, 2, 1))),
  bi_class = paste0(as.character(class_struc), '-', as.character(class_anim))
)


tmp <- biscale::bi_class_breaks(
  map_loc_bivar,
  x = `3dStruc_cnt`,
  y = `3dAnim_cnt`,
  style = "equal",
  dim = 3)

bivar_label <- list('bi_x'=c('0', '1', '5', '50', '268'), 
                    'bi_y'=c('0', '1', '3', '10', '120'))


map_bivar <- ggplot()+
  geom_sf(data=map_loc_bivar, mapping=aes(fill = bi_class), color="white", 
          size=0.1, show.legend = FALSE)+
  bi_scale_fill(pal="BlueYl", dim=4)+
  labs(title = "",
       subtitle =  "")+
  bi_theme()+
  geom_sf(data=admin, fill=NA, color="black", size=0.05)

legend <- bi_legend(pal = "BlueYl",
                    breaks = bivar_label,
                    dim = 4,
                    xlab = "Number of studies on 3D structure",
                    ylab = "Number of studies on 3D biodiversity",
                    size = 5.5,
                    arrows=FALSE)

finalPlot <- ggdraw() +
  draw_plot(map_bivar, 0, 0, 1, 1) +
  draw_plot(legend, x=0.67, y=0.55, width=0.28, height=0.28)

# finalPlot

ggsave(filename = "viz/bivar_3d_map.png",
       dpi=300,
       width = 12,
       height = 5,
       finalPlot)

# ========= Habitat types ==========
unique(df1$Habitat_Types)
# OMG this is not clean at all! Okay let's create a new data frame to hack this
dfhab <- df1 %>% select(c("ID", "Habitat_Types"))
dfhab <- dfhab %>% mutate(
  ifForest = ifelse(grepl("forest|pine|broad-leaved woods|douglas-fir|spruce|Yungas|Restinga|Campinarana|taiga|shelterbelt|Dry Chaco", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifWoodland = ifelse(grepl("woodland|Chaco Serrano|woody|woods|wooded|woodlot", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifGrassland = ifelse(grepl("grassland|prairie|great plains|herb|rangeland|moorland|pampas", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifSteppe = ifelse(grepl("steppe", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifShrubland = ifelse(grepl("sagebrush|shrub|thicket|canebrake|scrub|heathland|bush|moorland|maqui|brush", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifSavanna = ifelse(grepl("savanna|Cerrado|Campinarana|moorland", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifDesert = ifelse(grepl("desert|dune|sand|Caatinga", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifMountain = ifelse(grepl("mountain|alpine|hill|Sierra Nevada", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifAgNPast = ifelse(grepl("agro|agri|rice|cultivated|pasture|farm|crop|maize|arable|cereal", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifASP = ifelse(grepl("agrosilvopastoral|Montado|Dehesas", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifUrban = ifelse(grepl("urban|garden|park|green space|arena", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifRoad = ifelse(grepl("road|highway", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifPlantation = ifelse(grepl("plantation|commercial|coffee|rubber|vineyard|orchard|cotton field|timber harvest", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifRiparCoast = ifelse(grepl("riparian|bog|gallery|peat|wetland|marsh|riverbank|fen|Coastal|coastal|bay|island", Habitat_Types, ignore.case=TRUE), 1, 0),
  ifTundra = ifelse(grepl("tundra", Habitat_Types, ignore.case=TRUE), 1, 0)
)


dfhab <- dfhab %>% replace(is.na(.), 0) %>%
  mutate(sumval = rowSums(.[3:17]),
         ifOther = ifelse(sumval==0,1,0))

freq_hab <- dfhab %>% dplyr::summarise(across(where(is.numeric), ~sum(., na.rm=TRUE)))
freq_hab$sumval <- NULL
vec_count_hab <- as.numeric(freq_hab[1,])

# noeco <- dfhab %>% filter(sumval==0)

hab_names <- c("Forest", "Woodland", "Grassland", "Steppe", "Shrubland", "Savanna",  "Desert", "Mountain", "Agriculture/Pasture", "Agrosylvopastoral", "Urban", "Road", "Plantation",  "Riparian/Coastal", "Tundra", "Other")
vec_freq_hab_labels <- paste0(hab_names, " ", round(100*vec_count_hab/sum(vec_count_hab), digits=1), "%")

# try pie chart
#pie(vec_count_hab, labels=vec_freq_hab_labels, border = "white"
#    , col=colorRampPalette(brewer.pal(8, "Set2"))(15)
#    )

freq_hab_t <- transpose(freq_hab)
colnames(freq_hab_t) <- 'count'
freq_hab_t$name <- hab_names
freq_hab_t$label <- vec_freq_hab_labels
freq_hab_t$perc <- paste0(round(100*vec_count_hab/sum(vec_count_hab), digits=1), "%")

# Get the positions
df2 <- freq_hab_t %>% 
  mutate(csum = rev(cumsum(rev(count))), 
         pos = count/2 + lead(csum, 1),
         pos = if_else(is.na(pos), count/2, pos))

hab_p <- ggplot(df2, aes(x = "" , y = count, fill = fct_inorder(label))) +
  geom_col(width = 1, color = 1) +
  coord_polar(theta = "y") +
  scale_fill_manual(values = colorRampPalette(brewer.pal(8, "Set2"))(16)) +
  geom_label_repel(data = df2, force=1,
                   aes(y = pos, label = name),
                   size = 5, nudge_x = 1, show.legend = FALSE,
                   label.size = NA, segment.alpha=0.5, segment.linetype="dashed") +
  theme_void()+  
  theme(
    legend.title = element_text(size=16, margin=margin(b=10)),
    legend.text = element_text(size=12),
    legend.spacing.y=unit(10, 'inch'),
    legend.spacing.x=unit(10, 'inch')) +
  guides(fill = guide_legend(title = "Habitat Types", byrow=TRUE, theme(legend.spacing.y=unit(10, 'inch'))))

ggsave(filename='viz/habitat_type.png', hab_p, height=10, width=15)

# [not used] try lollipop chart
#ggplot(freq_hab_t, aes(x=name, y=count))+
#  geom_segment(aes(x=name, xend=name, y=0, yend=count), color="grey")+
#  geom_point(color="orange", size=4)+
#  theme_light()+
#  theme(
#    panel.grid.major.x = element_blank(),
#    panel.border = element_blank(),
#    axis.ticks.x = element_blank()
#  ) +
#  xlab("") +
#  ylab("Count")

# ======== Spatial extent ========
ext <- df1 %>% select('ID', 'clean_extent')
ext <- ext %>% mutate(
  ifSite = ifelse(grepl("site", clean_extent), 1, 0),
  ifPlot = ifelse(grepl("plot", clean_extent), 1, 0),
  ifStand = ifelse(grepl("stand", clean_extent), 1, 0),
  ifCrossing = ifelse(grepl("corssing|pass|bridge", clean_extent), 1, 0),
  ifLine = ifelse(grepl("line", clean_extent), 1, 0),
  ifUnknwon = ifelse(grepl("unknwon", clean_extent), 1, 0)
)

extractSize <- function(thestring){
  secs = unlist(strsplit(thestring, ";"))
  if(length(secs)==2){
    return(secs[2])
  } else if(grepl("ha|km|m|cm", secs[1])){
    return(secs[1])
  } else {
    return("")
  }
}


ext$size <- lapply(ext$clean_extent, extractSize)


options(scipen=999)
# change all units to ha
unifyUnits <- function(thestring){
  num = ""
  if(thestring!="" & !is.na(thestring)){
    secs = unlist(strsplit(thestring, " "))
    if(length(secs)==2){
      if(secs[2]=="ha"){
        num = as.character(ceiling(as.numeric(secs[1])))
      } else if(secs[2]=="km2"){
        num = as.character(ceiling(as.numeric(secs[1])*100))
      } else if(secs[2]=="m2"){
        num = as.character(ceiling(as.numeric(secs[1])/10000))
      } else {
        num = ""
      }
    } else{
      print(thestring)
      }
  } 
  return(num)
}

# get area information for each country
ext$size_ha <- lapply(ext$size, unifyUnits)
ext$size_ha <- as.numeric(ext$size_ha)
ext$size_km2 <- as.numeric(ext$size_ha)/100

ext_valid <- ext[ext$size_ha!="", ][c("ID", "size_ha", "size_km2")]
ext_valid <- ext_valid[!is.na(ext_valid$size_ha), ]

max(ext_valid$size_km2)

summary(ext_valid$size_km2)


ext_loc <- merge(loc, ext_valid, by="ID")
unique(ext_loc$Study_Country)

ext_loc_expanded <- do.call(rbind, Map(cbind, strsplit(ext_loc$Study_Country, ";"), ext_loc$size_km2))

ext_loc_expanded <- as.data.frame(ext_loc_expanded)
colnames(ext_loc_expanded) <- c("country", 'size_km2')
ext_loc_expanded$size_km2 = as.numeric(ext_loc_expanded$size_km2)

sum_size <- ext_loc_expanded %>%
  group_by(country) %>%
  summarise_at(vars(size_km2), list(mean_size = mean, min_size = min, 
                                   max_size = max, std_size = sd, 
                                   median_size = median))

sum_size$mean_size <- ceiling(sum_size$mean_size)

sum_size_count_freq <- as.data.frame(table(ext_loc_expanded$country))
colnames(sum_size_count_freq) <- c("country", "count")

sum_size <- merge(sum_size, sum_size_count_freq, by="country")


# keep countries with more than 5 papers

sum_size_5 <- sum_size %>% filter(count>=5)
sum_size_10 <- sum_size %>% filter(count>=10)

most_studies <- sum_size %>% filter(count>=18)

#  summarize for each continent
colnames(admin)
continent_info <- admin[c('NAME_EN','CONTINENT')]
continent_info$geometry <- NULL
ext_continent <- merge(ext_loc_expanded, continent_info, by.x='country', by.y='NAME_EN', all.x=TRUE)
unique(ext_continent$CONTINENT)

ctnt <- ext_continent[!is.na(ext_continent$CONTINENT),]
#df_ctnt_ext[nrow(df_ctnt_ext)+1] <- 

df_ctnt_ext <- ctnt %>%
  group_by(CONTINENT) %>%
  skim() %>% filter(skim_variable=='size_km2')
df_ctnt_ext <- df_ctnt_ext[c('CONTINENT', 'numeric.p0', 'numeric.mean', 'numeric.p50', 'numeric.p100', 'numeric.sd')]
colnames(df_ctnt_ext) <- c('CONTINENT', 'Min', 'Mean', 'Median', "Max", "SD")

# ======== Topic ========
df_topic <- df[c('if3dStruc', 'if3dAnim', 'ifCor', 'ifStrucAni', 'ifAniStruc')]
df_topic_sum <- as.data.frame(table(df_topic))
df_topic_sum <- df_topic_sum %>% filter(Freq>0)

# ===========================================================================
# ======= [version 2024] try creating a heatmap =======
#df_no_exo <- df_topic %>% filter(Exogenous==0) %>% select(!Exogenous)
#df_exo <- df_topic %>% filter(Exogenous==1) %>% select(!Exogenous)

# x axis: hab = 1, biodiv = 1, or both = 1
# y axis: cor + cause + aff = 0 | exo; cor = 1 the other 0 | exo; cause = 1 the other 0 | exo; aff = 1 the other 0 | exo

#df_topic <- df_topic %>% mutate(
#  xval = ifelse((Habitat==1 & Biodiversity == 1), 'Both', ifelse(
#    Habitat==1, 'Habitat', 'Biodiversity'
#  ))
#)

#df_topic <- df_topic %>% mutate(yval = 
#                                  ifelse(Correlate+Cause+Affected+Exogenous==0, '00', ifelse(
#                                    Correlate+Cause+Affected==0 & Exogenous==1, '01', ifelse(
#                                      Correlate==1 & Cause+Affected+Exogenous==0, '40', ifelse(
#                                        Correlate+Exogenous==2 & Cause+Affected==0, '41', ifelse(
#                                          Cause==1 & Correlate+Affected+Exogenous==0, '50', ifelse(
#                                            Cause+Exogenous==2 & Correlate+Affected==0, '51', ifelse(
#                                              Affected==1 & Correlate+Cause+Exogenous==0, '60', '61'
#                                            )
#                                          )
#                                        )
#                                      )  
#                                    ) 
#                                  ))
#)
# I deleted a bunch ....
#df_long_xy <- df_long_xy %>% mutate(
#  ifexo = ifelse(yval %in% c('00', '40', '50', '60'), 'No exogenous', 'Exogenous')
#)

# ===========================================================================
# ======= [version 2025] try creating a heatmap =======
df_topic <- df_topic %>% mutate(
  xval = ifelse((if3dStruc==1 & if3dAnim == 1), 'Both', ifelse(
    if3dStruc==1, 'Habitat', ifelse(if3dAnim==1, 'Biodiversity', 'unknown')
  ))
)

sum(df_topic$if3dAnim)

df_topic <- df_topic %>% mutate(
  yval = ifelse(ifCor+ifStrucAni+ifAniStruc==0, "1", ifelse(
    ifCor==1 & (ifStrucAni+ifAniStruc==0), "2", ifelse(
      ifStrucAni==1 & ifAniStruc==0, "3", ifelse(
        ifAniStruc==1 & ifStrucAni==0, "4", ifelse(
          ifStrucAni+ifAniStruc==2, "5", "unknown"
        )
      )
    )
  ))
)

df_long_xy <- as.data.frame(table(df_topic[c('xval', 'yval')])) %>% 
  mutate(xval=factor(xval, levels=c('Habitat', 'Both', 'Biodiversity')),
         yval=factor(yval, levels=c('5', '4', '3', '2', '1')),
         rel=ifelse(yval == '1', 'Itself', ifelse(
           yval == '2', 'Correlation', ifelse(
             yval == '3', 'Structure -> Biodiversity', ifelse(
               yval== '4', 'Biodiversity -> Structure', 'Feedback Loop')
           )
         )))

df_long_xy <- df_long_xy %>% mutate(
  rel=factor(rel, levels=c('Feedback Loop', 'Biodiversity -> Structure', 'Structure -> Biodiversity', 'Correlation', 'Itself'))
)

df_wide_xy <- reshape(df_long_xy, idvar='yval', v.names='Freq', timevar='xval', direction='wide')
# rownames(df_wide_xy) <- df_wide_xy$yval

#df_wide_xy$yval <- NULL

#colnames(df_wide_xy) <- c('biodiversity', 'both', 'habitat')
#df_wide_xy <- df_wide_xy[c('habitat', 'both', 'biodiversity')]

library(ggrepel)

# manual scale
#ggplot(df_long_xy, aes(xval, ifexo, fill=Freq))+
topic_p <- ggplot(df_long_xy, aes(xval, rel, fill=Freq))+
  geom_tile(aes(fill=Freq, width=0.95, height=0.95), size=2)+
  geom_text_repel(aes(label=Freq), size=5, family="Times", bg.color='white', bg.r=0.2, hjust=0.5, vjust=0.5, direction = "both", force = 0, box.padding = 0.5, point.padding = 0)+
  #scale_fill_viridis(discrete=FALSE)+
  scale_fill_gradientn(
    colours = c("#0d3b66", "#faf0ca","#f4d35e", "#ee964b", "#f95738"),
    values = scales::rescale(c(5,10,50,100,150,300)),
    name = 'Number of Papers'
  )+
  #facet_wrap(~rel, nrow=4, strip.position = "left")
  theme_minimal()+
  theme(axis.ticks.x=element_blank(),
        axis.ticks.y=element_blank(),
        axis.title.x=element_blank(),
        axis.text.x=element_text(face='bold', size=18, family="Times", color='black'),
        axis.text.y=element_text(family='Times', size=12),
        legend.text=element_text(family='Times', size=12),
        legend.title=element_text(family='Times', size=15),
        axis.title.y=element_blank(),
        panel.spacing.y=unit(0, 'lines'),
        panel.grid.major = element_blank(),
        #strip.text.y.left = element_text(angle=0),
        strip.text.y.left = element_text(face='bold', size=18, family='Times'),
        strip.placement = "outside")

ggsave(filename='viz/topic_numbers.png', topic_p, height=5, width=8)

# [not used] test creating a venn diagram
#venn.diagram(
#  x = as.list(df_topic %>% select(!Exogenous)),
#  category.names = c('Habitat', 'Biodiversity', 'Correlate', 'Cause', 'Affected'),
  #filename = 'viz/topic_venn_diagram.png',
  #output = TRUE
#)


# ===== Group 1 Habitat structure ======
df_hab <- df1 %>% filter(if3dStruc==1) %>% 
  select(all_of(c('ID', hab_dat_cols, hab_met_cols, 'year'))) %>%
  mutate(if_lidar=ifelse(`Method_Airborne.Lidar_GPT`==1 | `Method_Terrestrial.Lidar_GPT`==1 | `Method_Spaceborne.Lidar_GPT`==1, 1, 0),
         hab_data=ifelse(if_lidar==1 &`Method_Field.Sampling_GPT`==0, 'LiDAR Only',
                         ifelse(if_lidar==0 & `Method_Other.Remote.Sensing_GPT`==0 & `Method_Field.Sampling_GPT`==1, 'Field Only', ifelse(
                           if_lidar==0 & `Method_Other.Remote.Sensing_GPT`==1 & `Method_Field.Sampling_GPT`==1, 'Field and Other RS', 
                           ifelse(if_lidar==1&`Method_Field.Sampling_GPT`==1, 'LiDAR and Field', 'Other')))))


df_hab <- df_hab %>% mutate(
  hab_data=factor(hab_data, levels=c('Field Only', 'Field and Other RS', 'LiDAR and Field', 'LiDAR Only')
))

df_hab$year_5 <- 5*ceiling(df_hab$year/5)

hab_data_p <- ggplot(data=df_hab)+
  geom_histogram(aes(x=year_5, fill=hab_data),
                 bins=10, color='white', alpha=0.9)+
  scale_fill_manual('Data Type', values=c(
    '#f4d35e', 
    '#0d3b66',
    '#faf0ca',
    '#ee964b'))+
  # xlim(1970, 2030)+
  scale_x_continuous(breaks=(round(seq(1975, 2025, by=5),1)))+
  theme_bw()+
  theme(axis.ticks.x=element_blank(),
        axis.ticks.y=element_blank(),
        axis.title.y=element_text(face='bold', family='Times', size=18, color='black', margin=margin(t=0,r=10,b=0,l=0)),
        axis.title.x=element_text(face='bold', family='Times', size=18, color='black', margin=margin(t=10, r=0, b=0, l=0)),
        axis.text.x=element_text(family="Times", size=12, margin=margin(t=-5,r=0,b=0, l=0), hjust = -0.5),
        axis.text.y=element_text(family='Times', size=12),
        legend.text=element_text(family='Times', size=12),
        legend.title=element_text(family='Times', size=18),
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.border = element_blank()) +
  xlab('Publication Year') +
  ylab('Number of studies')
  

ggsave(filename='viz/habstruc_data.png', hab_data_p, width=8, height=5)

a <- df_hab[is.na(df_hab$hab_data), ]

df_hab_lidar <- df_hab %>% filter(if_lidar==1)

sum(df_hab$if_lidar)
nrow(df_hab[df_hab$hab_data =="Field Only", ])
sum(df_hab_lidar$Method_Spaceborne.Lidar_GPT)


# ===== Group 2 Biodiversity ======
taxa <- c('Birds', 'Bats', 'Primates', 'OtherMammals', 'Invertebrates', 'Reptiles', 'Amphibians')
df1 <- df1 %>% mutate(
  Birds = ifelse(grepl("birds|raptor", Animal_Taxa_Studied, ignore.case=TRUE), 1, 0),
  Bats = ifelse(grepl("bats", Animal_Taxa_Studied, ignore.case=TRUE), 1, 0),
  Primates = ifelse(grepl("primates", Animal_Taxa_Studied, ignore.case=TRUE), 1, 0),
  OtherMammals = ifelse(grepl("ungulates|ocelots|bobcats|coyotes|marsupials|rodents|other_mammals|small mammals|deer|jaguars|carnivores|lagomorphs|livestock|moose|lemurs", Animal_Taxa_Studied, ignore.case=TRUE), 1, 0),
  Invertebrates = ifelse(grepl("moth|insect|spider|arthropod|spider|orthopterans|anurans|bee|wasp|syrphids|carabids|beetles", Animal_Taxa_Studied, ignore.case=TRUE), 1, 0),
  Reptiles = ifelse(grepl("reptiles|lizards", Animal_Taxa_Studied, ignore.case=TRUE), 1, 0),
  Amphibians = ifelse(grepl("amphibians|frog|anuran", Animal_Taxa_Studied, ignore.case=TRUE), 1, 0)
)


df3d2dBio <- df1 %>% select(all_of(c('ID', 'year', 'if3dAnim', taxa)))


df3d2dbio_long <- data.frame(matrix(ncol=3, nrow=0))
colnames(df3d2dbio_long) <- c('ID', 'Taxa', 'if3dAnim')

for(i in 1:nrow(df3d2dBio)){
  thisrow = df3d2dBio[i,]
  thisid = thisrow$ID
  this3d = thisrow$if3dAnim
  for(col in taxa){
    if(thisrow[col]==1){
      df3d2dbio_long[nrow(df3d2dbio_long)+1, ] <- c(thisid, col, this3d)
    }
  }
}

df3d2dbio_long <- df3d2dbio_long %>% mutate(
  Taxa = ifelse(Taxa=="OtherMammals", "Other Mammals", Taxa)
)

df3d2dbio_long <- df3d2dbio_long %>% mutate(
  Taxa = factor(Taxa, levels=c("Birds", "Other Mammals", "Bats", "Primates", "Invertebrates", "Reptiles", "Amphibians")),
  if3dAnim = ifelse(if3dAnim==1, "3D", "2D")
)

nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Birds',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Other Mammals',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Bats',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Bats' & df3d2dbio_long$if3dAnim=='3D',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Primates',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Primates' & df3d2dbio_long$if3dAnim=='3D',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Reptiles',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Amphibians',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Amphibians' & df3d2dbio_long$if3dAnim=='3D',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Invertebrates',])
nrow(df3d2dbio_long[df3d2dbio_long$Taxa=='Invertebrates' & df3d2dbio_long$if3dAnim=='3D',])



taxa_p <- ggplot(data=df3d2dbio_long)+
  geom_histogram(aes(x=Taxa, fill=if3dAnim),
                 bins=10, color='white', alpha=0.9, stat = 'count')+
  scale_fill_manual('Data Type', values=c(
    #'#f4d35e', 
    '#0d3b66',
    #'#faf0ca',
    '#ee964b'))+
  # xlim(1970, 2030)+
  # scale_x_continuous(breaks=(round(seq(1980, 2025, by=5),1)))+
  theme_bw()+
  theme(axis.ticks.x=element_blank(),
        axis.ticks.y=element_blank(),
        axis.title.y=element_text(face='bold', family='Times', size=18, color='black', margin=margin(t=0,r=10,b=0,l=0)),
        axis.title.x=element_text(face='bold', family='Times', size=18, color='black', margin=margin(t=10, r=0, b=0, l=0)),
        axis.text.x=element_text(family="Times", size=12, margin=margin(t=-5,r=0,b=0, l=0)),
        axis.text.y=element_text(family='Times', size=12),
        legend.text=element_text(family='Times', size=12),
        legend.title=element_text(family='Times', size=18),
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.border = element_blank()) +
  xlab('Taxa')+
  ylab('Number of studies')


ggsave(filename='viz/taxa.png', taxa_p, height=5, width=10)


df_bio <- df1 %>% filter(if3dAnim==1) %>% select(all_of(c('ID','Animal_Taxa_Studied','Animal_Sampling_Methods', 'Animal_Major.Tasks_Metrics', 'Animal_Acoustic.Monitoring_Present', 'Animal_Vertical.Movement_Present', 'year'))) %>% mutate_if(is.numeric, ~replace_na(., 0))


# [not used] try creating a wordcloud on research tasks
#library(wordcloud)
#wordcloud(df1$Animal_Major.Tasks_Metrics)

#library(tm)
#library(SnowballC)

#dtm <- TermDocumentMatrix(df1$Animal_Major.Tasks_Metrics)
#m <- as.matrix(dtm)
#v <- sort(rowSums(m),decreasing=TRUE)
#d <- data.frame(word = names(v),freq=v)
#head(d, 10)

# ===========================================================================
# ======= [version 2024] biodiversity =======
unique(df_bio$Animal_Taxa_Studied)
unique(df1$Animal_Taxa_Studied)

hist(df_bio$`year`)
sum(df_bio$`OtherMammals`)
sum(df_bio$Bats)
sum(df_bio$Birds)
sum(df_bio$Reptiles)
sum(df_bio$Amphibians)
sum(df_bio$Invertebrates)
sum(df_bio$Primates)

df_bio_bird <- df_bio %>% filter(Birds==1) %>% adorn_totals('row')
df_bio_bats <- df_bio %>% filter(Bats==1) %>% adorn_totals('row')
df_bio_inv <- df_bio %>% filter(Invertebrates==1) %>% adorn_totals('row')
df_bio_rep <- df_bio %>% filter(Reptiles==1) %>% adorn_totals('row')
df_bio_amp <- df_bio %>% filter(Amphibians==1) %>% adorn_totals('row')
df_bio_other_m <- df_bio %>% filter(OtherMammals==1) %>% adorn_totals('row')
df_bio_prmts <- df_bio %>% filter(Primates==1) %>% adorn_totals('row')
# read in biodiversity data
df_bio_stats <- read_excel('data/lit_coding_241230.xlsx', sheet='Biodiversity')
df_bio_info <- read_excel('data/lit_coding_241230.xlsx', sheet='Bio-info')
# wide to long reshape
df_bio_stats_lng <- melt(setDT(df_bio_stats), id.vars=c('Taxon'), variable.name='Task')

tsk_lv <- c('movement', 'use of space', 'behaviors', 'functional trait', 'distribution and occupancy','life history', 'habitat preference', 'prevalence', 
            'richness and diversity', 'stratification and niche segregation', 'abundance and density', 'community composition and turnover', 'functional richness and diversity', 'community similarity',
             'acoustic characteristics', 'habitat suitability')


df_bio_stats_fn <- merge(df_bio_stats_lng, df_bio_info, by.x=c('Task'), by.y=c('Theme'), all.x=TRUE) %>% 
  mutate(Taxon = factor(Taxon, levels=c('Plants', 'Invertebrates', 'Reptiles', 'Amphibians', 'Other mammals', 'Bats','Bird')),
         Task = factor(Task, levels=tsk_lv)
         )

labels <- levels(df_bio_stats_fn$Taxon)
li_brks <- c(1,2,3,4,5,6,7,8,10,11,12,13,14,15,17,18)
df_bio_stats_fn <- df_bio_stats_fn %>% arrange(factor(Task, levels=tsk_lv))
df_bio_stats_fn$aux <- rep(li_brks, times = table(df_bio_stats_fn$Task))

# heatmap
ggplot(df_bio_stats_fn, aes(x=aux, y=Taxon, fill=value))+
  geom_tile(aes(fill=value, width=0.95, height=0.95), size=2)+
  #scale_fill_viridis(discrete=FALSE)+
  scale_fill_gradientn(
    colours = c("#0d3b66", "#faf0ca","#f4d35e", "#ee964b", "#f95738"),
    values = scales::rescale(c(0,1,5,15,30)),
    name = 'Count'
  )+
  scale_x_discrete(breaks=li_brks, labels=levels(df_bio_stats_fn$Task), limits=li_brks)+
  theme_minimal()+
  #facet_wrap(~Level, ncol=3)+
  theme(axis.ticks.x=element_blank(),
        axis.ticks.y=element_blank(),
        axis.title.x=element_blank(),
        axis.text.x=element_text(size=10, family="Times", angle=90),
        #axis.text.x=element_blank(),
        axis.text.y=element_text(face='bold', family='Times', size=12, color='black'),
        legend.text=element_text(family='Times', size=12),
        legend.title=element_text(family='Times', size=18),
        axis.title.y=element_blank(),
        panel.spacing.y=unit(0, 'lines'),
        panel.grid.major = element_blank(),
        panel.grid.minor = element_blank(),
        #strip.text.y.left = element_text(angle=0),
        strip.text.y.left = element_text(face='bold', size=18, family='Times'),
        strip.placement = "outside")


sum((df_bio_stats_fn %>% filter(Level=='population'))$value)
sum((df_bio_stats_fn %>% filter(Level=='community'))$value)
sum((df_bio_stats_fn %>% filter(Level=='ecosystem'))$value)
# ===========================================================================
# ======= [version 2025] biodiversity =======
# Taxa

unique(df_bio$Animal_Taxa_Studied)


clean <-function(col){
  li <- as.list(col)
  li <- li[!is.na(li)]
  str_li <- paste(unlist(li), sep=';', collapse=';')
  
  li1 <- as.list(strsplit(str_li, ';')[[1]])
  df1 <- t(as.data.frame(li1))
  freq <- as.data.frame(table(df1))
  return(freq)
}


unique(df_bio$Animal_Taxa_Studied)
