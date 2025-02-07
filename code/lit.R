# Process literature
# script originally built for generating figures for landscape sustainability final term paper
# author: Wenxin Yang
# date: 11.23.2023
# version: 01/07/2025

pkgs <- c('plyr', 'tidyverse', 'sf', 'biscale', 'hrbrthemes', 'dplyr', 'tidyr',
          'networkD3', 'RColorBrewer', 'VennDiagram', 'cowplot', 'stringr', 'readxl',
          'viridis', 'janitor', 'data.table')

lapply(pkgs, library, character.only=TRUE)

getwd()

# ====== preprocessing steps ======
df0 <- read_excel('data/lit_coding_241230.xlsx', sheet='Journal articles')
colnames(df0) <- df0[1,]
df <- df0[-1,]
colnames(df)

# change varaible type to numeric
# topical cols
top_cols <- c('Habitat', 'Biodiversity', 'Correlate', 'Cause', 'Affected',
              'Exogenous')
# habitat data cols
hab_dat_cols <- c('Field veg data', 'Terrestrial LiDAR', 'Drone LiDAR', 'Airborne LiDAR', 'Other LiDAR', 'Spaceborne LiDAR', 'UAV SAR', 'airplane/drone optical', 'Optical', 'Other hab data')
# habitat metrics cols
hab_met_cols <- c('Cover', 'Height', 'Horizontal var.', 'Vertical var.')

# biodiversity levels
bio_lev_cols <- c('Individual', 'Population', 'Community', 'Ecosystem/landscape??')
# studied species
bio_spe_cols <- c('Other mammals', 'Bats', 'Birds', 'Reptiles', 'Amphibians', 'Invertebrates', 'Plants') # other species
# biodiversity tasks
bio_tsk_cols <- c('Species richness', 'Species diversity', 'Functional diversity', 'Species prevalence', 'Species abundance', 'Species absence /presence', 'Speices distribution', 'SDM', 'Habitat occupancy', 'Species survival/mortality', 'Predation rate', 'Movement', 'Habitat suitability', 'Vertical stratification', 'Community similarity/dis-', 'species trait') # other tasks


for (col in c(top_cols, hab_dat_cols, hab_met_cols, bio_lev_cols, bio_spe_cols, bio_tsk_cols, 'Publication Year')){
  print(col)
  df[col] <- as.numeric(df[[col]])
}

str(df)

# replace NA values with 0s for numeric columns
df <- df %>% mutate_if(is.numeric, ~replace_na(., 0))


 # ======== Topic ========
df_topic <- df[c('Habitat', 'Biodiversity', 'Correlate', 'Cause', 'Affected', 'Exogenous')]
df_topic_sum <- as.data.frame(table(df_topic))
df_topic_sum <- df_topic_sum %>% filter(Freq>0)

df_no_exo <- df_topic %>% filter(Exogenous==0) %>% select(!Exogenous)
df_exo <- df_topic %>% filter(Exogenous==1) %>% select(!Exogenous)


# test creating a heatmap
# x axis: hab = 1, biodiv = 1, or both = 1
# y axis: cor + cause + aff = 0 | exo; cor = 1 the other 0 | exo; cause = 1 the other 0 | exo; aff = 1 the other 0 | exo
df_topic <- df_topic %>% mutate(
  xval = ifelse((Habitat==1 & Biodiversity == 1), 'Both', ifelse(
    Habitat==1, 'Habitat', 'Biodiversity'
  ))
)

df_topic <- df_topic %>% mutate(yval = 
    ifelse(Correlate+Cause+Affected+Exogenous==0, '00', ifelse(
    Correlate+Cause+Affected==0 & Exogenous==1, '01', ifelse(
      Correlate==1 & Cause+Affected+Exogenous==0, '40', ifelse(
        Correlate+Exogenous==2 & Cause+Affected==0, '41', ifelse(
          Cause==1 & Correlate+Affected+Exogenous==0, '50', ifelse(
            Cause+Exogenous==2 & Correlate+Affected==0, '51', ifelse(
              Affected==1 & Correlate+Cause+Exogenous==0, '60', '61'
            )
          )
      )
    )  
    ) 
  ))
)

df_long_xy <- as.data.frame(table(df_topic[c('xval', 'yval')])) %>% 
  mutate(xval=factor(xval, levels=c('Habitat', 'Both', 'Biodiversity')),
         yval=factor(yval, levels=c('61', '60', '51', '50', '41', '40', '01', '00')),
         rel=ifelse(yval %in% c('00','01'), 'Itself', ifelse(
           yval %in% c('40', '41'), 'Correlation', ifelse(
             yval %in% c('50', '51'), 'Cause', 'Affected'
           )
         )),
         rel=factor(rel, levels=c('Itself', 'Correlation', 'Cause', 'Affected')))
df_long_xy <- df_long_xy %>% mutate(
  ifexo = ifelse(yval %in% c('00', '40', '50', '60'), 'No exogenous', 'Exogenous')
)

df_wide_xy <- reshape(df_long_xy, idvar='yval', v.names='Freq', timevar='xval',
                      direction='wide')
rownames(df_wide_xy) <- df_wide_xy$yval
df_wide_xy$yval <- NULL
colnames(df_wide_xy) <- c('biodiversity', 'both', 'habitat')
df_wide_xy <- df_wide_xy[c('habitat', 'both', 'biodiversity')]

# manual scale
ggplot(df_long_xy, aes(xval, ifexo, fill=Freq))+
  geom_tile(aes(fill=Freq, width=0.95, height=0.95), size=2)+
  #scale_fill_viridis(discrete=FALSE)+
  scale_fill_gradientn(
    colours = c("#0d3b66", "#faf0ca","#f4d35e", "#ee964b", "#f95738"),
    values = scales::rescale(c(0,1,5,10,30,100)),
    name = 'Count'
  )+
  facet_wrap(~rel, nrow=4, strip.position = "left")+
  theme_minimal()+
  theme(axis.ticks.x=element_blank(),
        axis.ticks.y=element_blank(),
        axis.title.x=element_blank(),
        axis.text.x=element_text(face='bold', size=18, family="Times", color='black'),
        axis.text.y=element_text(family='Times', size=12),
        legend.text=element_text(family='Times', size=12),
        legend.title=element_text(family='Times', size=18),
        axis.title.y=element_blank(),
        panel.spacing.y=unit(0, 'lines'),
        panel.grid.major = element_blank(),
        #strip.text.y.left = element_text(angle=0),
        strip.text.y.left = element_text(face='bold', size=18, family='Times'),
        strip.placement = "outside")


# test creating a venn diagram
venn.diagram(
  x = as.list(df_topic %>% select(!Exogenous)),
  category.names = c('Habitat', 'Biodiversity', 'Correlate', 'Cause', 'Affected'),
  filename = 'viz/topic_venn_diagram.png',
  output = TRUE
)


# ===== Group 1 Habitat structure ======
df_hab <- df %>% filter(Habitat==1) %>% 
  select(all_of(c(hab_dat_cols, hab_met_cols, 'Publication Year'))) %>%
  mutate(if_lidar=ifelse(`Terrestrial LiDAR`==1 | `Drone LiDAR`==1 | `Airborne LiDAR`==1 | `Spaceborne LiDAR`==1 | `Other LiDAR`==1, 1, 0),
         hab_data=ifelse(if_lidar==1&`Field veg data`==0, 'LiDAR Only',
                           ifelse(if_lidar==0 & `Field veg data`==1, 'Field Only',
                                  ifelse(if_lidar==1&`Field veg data`==1, 'LiDAR and Field', 'Other'))),
         hab_data=factor(hab_data, levels=c('Other', 'Field Only', 'LiDAR and Field', 'LiDAR Only')))

df_hab$year_5 <- 5*round(df_hab$`Publication Year`/5)

ggplot(data=df_hab)+
  geom_histogram(aes(x=`Publication Year`, fill=hab_data),
                 bins=10, color='white', alpha=0.9)+
  scale_fill_manual('Data Type', values=c('#0d3b66', '#faf0ca', '#f4d35e', '#ee964b'))+
  xlim(1970, 2030)+
  scale_x_continuous(breaks=(round(seq(1980, 2025, by=5),1)))+
  theme_bw()+
  theme(axis.ticks.x=element_blank(),
        axis.ticks.y=element_blank(),
        axis.title.y=element_blank(),
        axis.title.x=element_text(face='bold', family='Times', size=18, color='black', margin=margin(t=10, r=0, b=0, l=0)),
        axis.text.x=element_text(family="Times", size=12, margin=margin(t=-5,r=0,b=0, l=0)),
        axis.text.y=element_text(family='Times', size=12),
        legend.text=element_text(family='Times', size=12),
        legend.title=element_text(family='Times', size=18),
        panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.border = element_blank())
  
df_hab_lidar <- df_hab %>% filter(if_lidar==1)

sum(df_hab$Height)

# ===== Group 2 Biodiversity ======
df_bio <- df %>% filter(Biodiversity==1) %>% select(all_of(c(bio_lev_cols, bio_spe_cols, 'Other species', bio_tsk_cols, 'Other tasks', 'Publication Year'))) %>% mutate_if(is.numeric, ~replace_na(., 0))

hist(df_bio$`Publication Year`)
sum(df_bio$`Other mammals`)
sum(df_bio$Bats)
sum(df_bio$Birds)
sum(df_bio$Reptiles)
sum(df_bio$Amphibians)
sum(df_bio$Invertebrates)
sum(df_bio$Plants)

df_bio_bird <- df_bio %>% filter(Birds==1) %>% adorn_totals('row')
df_bio_bats <- df_bio %>% filter(Bats==1) %>% adorn_totals('row')
df_bio_inv <- df_bio %>% filter(Invertebrates==1) %>% adorn_totals('row')
df_bio_rep <- df_bio %>% filter(Reptiles==1) %>% adorn_totals('row')
df_bio_amp <- df_bio %>% filter(Amphibians==1) %>% adorn_totals('row')
df_bio_other_m <- df_bio %>% filter(`Other mammals`==1) %>% adorn_totals('row')
df_bio_plt <- df_bio %>% filter(`Plants`==1) %>% adorn_totals('row')


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
