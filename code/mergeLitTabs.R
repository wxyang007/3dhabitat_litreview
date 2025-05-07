# this script is for merging the three tabs together

pkgs <- c('dplyr', 'tidyr', 'readxl', 'writexl', 'caret')
lapply(pkgs, library, character.only=TRUE)

# this is the original search (focused search)
tab1 <- read_excel('lit/lit_coding_241230.xlsx', sheet='Journal articles')
colnames(tab1) <- tab1[1,]
tab1 <- tab1[-1,] %>% select("ID", "Title") %>%
  mutate(source = "search1",
         `Document Type` = "Article")
# colnames(tab1)

# this is the training set
tab2 <- read_excel('lit/Boosted lit search/Jan2025/newfiles5_train.xlsx') %>% 
  filter(ifKeep==1) %>% 
  select("id", "Article Title", "Document Type") %>%
  dplyr::rename(ID=id, Title=`Article Title`) %>%
  mutate(source='search2train',  # Jan search
         ID=sprintf("J%04d", ID)) 
colnames(tab2)

# this is the pred set
tab3_pred <- read_excel('lit/Boosted lit search/Jan2025/newfiles5_pred_predictions_unq.xlsx')
tab3_raw <- read_excel('lit/Boosted lit search/Jan2025/newfiles5_pred.xlsx') %>% 
  select("id", "Article Title", "Document Type") %>% 
  dplyr::rename(Title=`Article Title`)

tab3 <- merge(tab3_pred, tab3_raw, by="Title") %>%
  filter(Prediction=='keep') %>%
  dplyr::rename(ID=id) %>%
  mutate(source='search2pred', # Jan search
         ID=sprintf("J%04d", ID)) %>%
  select(-Prediction)

colnames(tab3_raw)

# merge them all
tab <- rbind(tab1, tab2, tab3)
length(unique(tab$Title)) # 26 duplicates

# get duplicates
li_article <- tab$Title
li_dup <- li_article[duplicated(li_article)]
li_dup


tab <- tab %>%
  mutate(ifDup = ifelse(Title %in% li_dup, 1, 0))

duptab <- tab %>% filter(ifDup==1) # check

# remove duplicates
tab <- tab %>% filter(!(ifDup==1 & source=='search1')) %>%
  select(-ifDup)

# split into review vs non review
tab <- tab %>% mutate(ifRev = ifelse(grepl("Review", `Document Type`), 1, 0))
tab_rev <- tab %>% filter(ifRev==1)
tab_article <- tab %>% filter(ifRev==0)

write_xlsx(tab_article, 'lit/AllJan25/merged_lit_2501.xlsx')


# add doi info back into this
tab_article <- read_xlsx('lit/AllJan25/merged_lit_2501.xlsx')
to_download <- tab_article %>% slice(707:n())

raw_newfile <- read_xlsx('lit/Boosted lit search/Jan2025/newfiles5.xlsx') %>% select(`Article Title`, DOI)
to_download <- merge(to_download, raw_newfile, by.x="Title", by.y="Article Title", all.x=TRUE)

to_download_nodoi <- to_download %>% filter(is.na(DOI))
to_download_doi <- to_download %>% filter(!is.na(DOI))

write_xlsx(to_download_doi, 'lit/AllJan25/paper_dois.xlsx')


# ================= create a list of papers not downloaded ===========
results_excel <- read_xlsx('lit/AllJan25/bulk_papers/download_results.xlsx')
unique(results_excel$Status)
failed_papers <- results_excel %>% filter(Status!="PDF Downloaded") %>% 
  select(ID, Title, DOI)
write_xlsx(failed_papers, 'lit/AllJan25/bulk_papers/scihub_dlwd_info.xlsx')


# ====== randomly select 100 papers to validate generative ai results =========
# note, because one paper was irrelevant after reading it, it was removed
df_merged <- read_xlsx('lit/AllJan25/merged_lit_2501.xlsx') %>%
  mutate_all(~replace(., is.na(.), 0)) %>%
  filter(ifProblem != 100)
df_merged <- df_merged %>% mutate(
  ifbridge = ifelse(grepl('canopy bridge', Title), 1, 0),
  ifpass = ifelse(grepl('passes|pass ', Title), 1, 0)
)

nrow(df_merged %>% filter(ifbridge==1))
nrow(df_merged %>% filter(ifpass==1))

bridge <- df_merged %>% filter(ifbridge==1)
bridge$newid <- 1:nrow(bridge)
pass <- df_merged %>% filter(ifpass==1)
pass$newid <- 1:nrow(pass)
other <- df_merged %>% filter(ifbridge+ifpass==0)
other$newid <- 1:nrow(other)

set.seed(226)
bridge_paper <- sample(1:nrow(bridge), 1)
pass_paper <- sample(1:nrow(pass), 1)
rand_papers <- sample(1:nrow(other), 98)

all_selected <- rbind(bridge[bridge_paper, ], pass[pass_paper, ], other[rand_papers,])

write_xlsx(all_selected, 'lit/AllJan25/merged_lit_100rand_val_2501.xlsx')

# ======= update merged_lit download info =======
raw_merged <- read_xlsx('lit/AllJan25/merged_lit_dwldInfo_2501.xlsx') %>% 
  mutate(ifDownloaded = ifelse(source=='search1', 1, 0))
folder_manual <- 'lit/AllJan25/manual_papers/'
folder_bulk <- 'lit/AllJan25/bulk_papers/'
li_manual1 <- list.files(file.path(folder_manual, 'papers1'))
li_manual2 <- list.files(file.path(folder_manual, 'papers2'))
li_bulk1 <- list.files(file.path(folder_bulk, 'downloaded_papers1'))
li_bulk2 <- list.files(file.path(folder_bulk, 'downloaded_papers2'))

li_dwld <- c(substr(li_manual1, 1, 5), substr(li_manual2, 1, 5), 
             substr(li_bulk1, 1, 5), substr(li_bulk2, 1, 5))
li_dwld <- li_dwld[!duplicated(li_dwld)]

raw_merged <- raw_merged %>% 
  mutate(ifDownloaded = ifelse(ID %in% li_dwld, 1, ifDownloaded))

getPath <- function(theid, thelist, thefolder, thesubfolder){
  thename <- thelist[startsWith(thelist, theid)]
  thepath <- file.path(thefolder, thesubfolder, thename)
  return(as.character(thepath))
}

getDwldPath <- function(theid){
  if(theid %in% substr(li_manual1, 1, 5)){
    thepath <- getPath(theid, li_manual1, folder_manual, 'papers1')
  } else if(theid %in% substr(li_manual2, 1, 5)) {
    thepath <- getPath(theid, li_manual2, folder_manual, 'papers2')
  } else if(theid %in% substr(li_bulk1, 1, 5)){
    thepath <- getPath(theid, li_bulk1, folder_bulk, 'downloaded_papers1')
  } else if(theid %in% substr(li_bulk2, 1, 5)){
    thepath <- getPath(theid, li_bulk2, folder_bulk, 'downloaded_papers2')
  } else {
    thepath <- ""
  }
  return(thepath)
}

raw_merged$path <- apply(raw_merged['ID'], MARGIN=1, FUN=getDwldPath)


write_xlsx(raw_merged, 'lit/AllJan25/merged_lit_dwldInfo_2501.xlsx')

codefile <- read_excel('lit/AllJan25/merged_lit_100rand_val_codebook_2501.xlsx')
li_selected <- unique(codefile$ID)


moveFile <- function(theid, thedf, thedir){
  thepath <- (thedf %>% filter(ID==theid))$path[[1]]
  print(paste0('start working on ', theid))
  if(!identical(thepath, character(0))){
    if((file.exists(thepath)) & (!is.na(thepath))){
      file.copy(thepath, file.path(thedir, paste0(theid, '.pdf')), overwrite = TRUE)
      print('done!')
    }
    else {print('no path')}
  }
}
raw_merged$path <- apply(raw_merged['ID'], MARGIN=1, FUN=getDwldPath)
sapply(li_selected, moveFile, thedf=raw_merged, thedir='data/pdfs/')

# ========== move accepted files in search 1 to the final dir ==========
search1_files <- raw_merged %>% filter(source=='search1') %>% 
  mutate(nchars = nchar(ID),
         ID = ifelse(nchars==1, paste0("00", ID), ifelse(nchars==2, paste0("0", ID), ID)))
li_search1 <- list.files(file.path('lit/Initial search/'))

getS1Path <- function(theid){
  thepath <- getPath(theid, li_search1, 'lit', 'Initial search')
}

search1_files$path <- apply(search1_files['ID'], MARGIN=1, FUN=getS1Path)
li_s1_move = unique(search1_files$ID)
sapply(li_s1_move, moveFile, thedf=search1_files, thedir='data/pdfs/')


# check what is left
file_copied <- substr(list.files('data/pdfs'), 1, 5)
setdiff(file_copied, li_selected)
setdiff(li_selected, file_copied)

# ========= remove plant only papers =======
id_remove <- c('R2A3', '420', '44', '76', '135', '146', '149', '274', '358', '377', '381',
               '411', '441', '459', '472', '522', '548', 'C16')

raw_merged <- read_xlsx('lit/AllJan25/merged_lit_2501.xlsx') %>% 
  filter(!ID %in% id_remove)
write_xlsx(raw_merged, 'lit/AllJan25/merged_lit_2501.xlsx')

raw_dwld_info <- read_xlsx('lit/AllJan25/merged_lit_dwldInfo_2501.xlsx') %>% 
  filter(!ID %in% id_remove)
write_xlsx(raw_merged, 'lit/AllJan25/merged_lit_dwldInfo_2501.xlsx')
