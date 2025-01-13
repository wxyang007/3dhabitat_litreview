library(readxl)
library(tmap)
library(plyr)
library(tidyverse)
library(sf)
library(biscale)
library(hrbrthemes)
library(dplyr)
library(tidyr)
library(networkD3)
library(RColorBrewer)
library(VennDiagram)
library(RColorBrewer)
library(cowplot)
library(stringr)

getwd()
df0 <- read_excel('data/lit_coding_0828.xlsx')
colnames(df0) <- df0[1,]
df0 <- df0[-c(1), ]

df <- df0


# ===== year published ======
unique(df$`Publication Year`)
df_yr <- as.data.frame(table(df$`Publication Year`))
colnames(df_yr) <- c("Year", "Number of Papers")
ggplot(data=df_yr, aes(x=Year, y=`Number of Papers`, group=1))+
  geom_line(color='grey')+
  geom_point(shape=16, color='#69b3a2', fill='#69b3a2',size=6)+
  scale_y_continuous(breaks=c(2, 4, 6, 8, 10)) +
  theme_ipsum()


# ===== locations ======
# pass
clean <-function(col){
  li <- as.list(col)
  li <- li[!is.na(li)]
  str_li <- paste(unlist(li), sep=';', collapse=';')
  
  li1 <- as.list(strsplit(str_li, ';')[[1]])
  df1 <- t(as.data.frame(li1))
  freq <- as.data.frame(table(df1))
  return(freq)
}

freq_loc <- clean(df$Country)
colnames(freq_loc) <- c('country', 'study_area_cnt')

freq_loc$name_en <- freq_loc$country
freq_loc$name_en <- as.character(freq_loc$name_en)
freq_loc[freq_loc$country=='China', ]$name_en <- "People's Republic of China"
freq_loc[freq_loc$country %in% c('UK', 'UK?', 'England', 'Scotland'), ]$name_en <- "United Kingdom"
freq_loc[freq_loc$country=='US', ]$name_en <- "United States of America"
freq_loc[freq_loc$country=='Cameron', ]$name_en <- "Cameroon"
freq_loc[freq_loc$country=='France?', ]$name_en <- "France"
freq_loc[freq_loc$country=='Korea', ]$name_en <- "South Korea"
freq_loc[freq_loc$country %in% c('Czechia', 'Czech republic'), ]$name_en <- "Czech Republic"
freq_loc[freq_loc$country=='Republic of Panama', ]$name_en <- "Panama"
freq_loc[freq_loc$country %in% c('Not mentioned', 'None', 'not applicable'), ]$name_en <- "N.A."
freq_loc[freq_loc$country %in% c('global', 'Global', 'Global literature written in English'), ]$name_en <- "Global"

freq_loc1 <- aggregate(freq_loc$study_area_cnt, by=list(name_en=freq_loc$name_en), FUN=sum)


admin <- read_sf('/Users/wenxinyang/Desktop/Dissertation/DATA/WB_countries_Admin0_10m/WB_countries_Admin0_10m.shp')
df_loc <- data.frame(freq_loc1, stringsAsFactors = FALSE)

map_loc <- merge(admin, df_loc, by.x='NAME_EN', by.y='name_en'
                 #,all.y=TRUE
)
map_loc <- map_loc[c('NAME_EN', 'x')]
colnames(map_loc) <- c('NAME_EN', 'Count', 'geometry')
map_loc[is.na(map_loc)] <- 0

df_map_loc <- map_loc
df_map_loc$geometry <- NULL
# write.csv(df_map_loc, 'location_counts.csv')


freq_map <- tm_shape(map_loc) +
  tm_fill("Count", fill.scale=tm_scale_intervals(breaks=c(1,3,10,15,20, 65)))+
  tm_borders()+
  tm_shape(admin)+
  tm_borders()

tmap_save(tm = freq_map, filename = "viz/country_frequency_map.png")

# pie(map_loc$study_area_cnt, labels = map_loc$NAME_EN)

# ===== taxon ======
df[is.na(df$`Other mammals`), ]$`Other mammals` <- '0'
df$`Other mammals` <- as.numeric(df$`Other mammals`)
num_other_mammals <- sum(df$`Other mammals`)

df[is.na(df$Bats), ]$Bats <- '0'
df$Bats <- as.numeric(df$Bats)
num_bats <- sum(df$Bats)

df[is.na(df$Birds), ]$Birds <- '0'
df$Birds <- as.numeric(df$Birds)
num_birds <- sum(df$Birds)

df[is.na(df$Reptiles), ]$Reptiles <- '0'
df$Reptiles <- as.numeric(df$Reptiles)
num_reptiles <- sum(df$Reptiles)

df[is.na(df$Amphibians), ]$Amphibians <- '0'
df$Amphibians <- as.numeric(df$Amphibians)
num_amphibians <- sum(df$Amphibians)

df[is.na(df$Invertebrates), ]$Invertebrates <- '0'
df$Invertebrates <- as.numeric(df$Invertebrates)
num_invertebrates <- sum(df$Invertebrates)

df[is.na(df$Plants), ]$Plants <- '0'
df$Plants <- as.numeric(df$Plants)
num_plants <- sum(df$Plants)

df_taxon <- data.frame(taxa=c('Other mammals', 'Bats', 'Birds', 'Reptiles', 
                              'Amphibians', 'Invertebrates', 'Plants'),
                       count=c(num_other_mammals, num_bats, num_birds, 
                               num_reptiles, num_amphibians, num_invertebrates, 
                               num_plants))

coul <- brewer.pal(5, "Set2") 
barplot(height=data$value, names=data$name, col=coul )
barplot(height=df_taxon$count, names=df_taxon$taxa, border="white", col=coul )
