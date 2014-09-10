from ome import base, components
from ome.loading import component_loading

def load_genomes():
    
    component_loading.load_genbank('NC_002745.gbk', base, components) #S. aureus iSB619         Bacteria/Staphylococcus_aureus_N315_uid57837 
    component_loading.load_genbank('NC_000962.gbk', base, components) #M. tuberculosis iNJ661   Bacteria/Mycobacterium_tuberculosis_H37Rv_uid57777
    component_loading.load_genbank('NC_000915.gbk', base, components) #H. pylori iIT341         Bacteria/Helicobacter_pylori_26695_uid57787
    component_loading.load_genbank('NC_007355.gbk', base, components) #M. barkeri iAF692        Bacteria/Methanosarcina_barkeri_Fusaro_uid57715
    component_loading.load_genbank('NC_002947.gbk', base, components) #P. putida iJN746         Bacteria/Pseudomonas_putida_KT2440_uid57843     Note: the grmit db contains locus ids that are not non existent in ncbi
    component_loading.load_genbank('hs_alt_HuRef_chr1.gbk', base, components)
    
"""
missing in ncbi files
pWW0_128 iJN746
pWW0_131 iJN746
pWW0_097 iJN746
pWW0_128 iJN746
pWW0_131 iJN746
pWW0_097 iJN746
pWW0_091 iJN746
pWW0_091 iJN746
pWW0_090 iJN746
pWW0_090 iJN746
pWW0_093 iJN746
pWW0_100 iJN746
pWW0_101 iJN746
pWW0_102 iJN746
pWW0_128 iJN746
pWW0_131 iJN746
pWW0_099 iJN746
pWW0_097 iJN746
pWW0_099 iJN746
pWW0_099 iJN746
pWW0_096 iJN746
pWW0_096 iJN746
pWW0_095 iJN746
pWW0_095 iJN746
pWW0_095 iJN746
pWW0_092 iJN746
pWW0_092 iJN746
pWW0_092 iJN746
pWW0_100 iJN746
pWW0_102 iJN746
pWW0_101 iJN746
pWW0_130 iJN746
pWW0_129 iJN746
pWW0_094 iJN746
pWW0_094 iJN746
pWW0_094 iJN746
pWW0_100 iJN746
pWW0_102 iJN746
pWW0_101 iJN746
pWW0_130 iJN746
pWW0_129 iJN746
pWW0_127 iJN746
PP_3739 iJN746
PP_3739 iJN746
pWW0_130 iJN746
pWW0_129 iJN746
HP0903 iIT341
HP0093 iIT341
HP0094 iIT341
HP0905 iIT341
Rv1755c iNJ661
Rv2233 iNJ661
Rv1755c iNJ661
Rv0618 iNJ661
Rv0619 iNJ661
Rv2322c iNJ661
Rv2321c iNJ661
Mbar_A3662 iAF692
MBd0198 iAF692
Mbar_A0379 iAF692
MBd3024 iAF692
MBd0275 iAF692
MBd3023 iAF692
MBd0274 iAF692
MBd4270 iAF692
Mbar_A0628 iAF692
Mbar_A1948 iAF692
MBd1413 iAF692
Mbar_A3605 iAF692
MBd3608 iAF692
Mbar_A1506 iAF692
Mbar_A0991 iAF692
MBd3435 iAF692
MBd1561 iAF692
Mbar_A3633 iAF692
MBd4022 iAF692
MBd4025 iAF692
MBd1438 iAF692
MBd0933 iAF692
Mbar_A1502 iAF692
MBd3602 iAF692
"""

if __name__ == '__main__':
    load_genomes()
