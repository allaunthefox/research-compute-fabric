import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')
#Load CSV
Sample=pd.read_csv("populations.csv", index_col=False)

#Calculating genotype frequencies
AA_list = []
Aa_list = []
aa_list = []

def calculate_genotype_frequencies(p,q):
    AA = round(p**2,2)
    Aa = round(2*p*q,2)
    aa = round(q**2,4)

    return AA,Aa,aa

for index, row in Sample.iterrows():
    p = row['Allele_A_Freq']
    q = row['Allele_a_Freq']

    AA, Aa, aa = calculate_genotype_frequencies(p, q)

    AA_list.append(AA)
    Aa_list.append(Aa)
    aa_list.append(aa)

Sample['AA']=AA_list
Sample['Aa']=Aa_list
Sample['aa']=aa_list

#Output csv
Sample.to_csv("Output.csv", index=False)

#Get available data 
available_genes = pd.Series(Sample['Gene'].unique())
available_populations = pd.Series(Sample['Population'].unique())
available_genotypes = ['AA', 'Aa', 'aa']

#GRAPH 1
def GenotypeFrequencyComparisonplot(gene):
    df_gene = Sample[Sample["Gene"] == gene]
    
    populations = df_gene["Population"].values
    AA_vals=df_gene["AA"].values
    Aa_vals=df_gene["Aa"].values
    aa_vals=df_gene["aa"].values

    x = np.arange(len(populations))
    width=0.25

    bar_AA=plt.bar(x-width, AA_vals, width, label="AA")
    bar_Aa=plt.bar(x, Aa_vals,width, label="Aa")
    bar_aa=plt.bar(x+width, aa_vals,width, label="aa")

    for i in range(len(populations)):
        plt.text(x[i]-width, AA_vals[i]+0.01, f"{AA_vals[i]:.2f}", ha='center', fontsize=9)
        plt.text(x[i], Aa_vals[i]+0.02, f"{Aa_vals[i]:.2f}", ha='center', fontsize=9)
        plt.text(x[i]+width, aa_vals[i]+0.02, f"{aa_vals[i]:.4f}", ha='center', fontsize=9)


    
    plt.xticks(x,populations)
    plt.title(f"Variation of genotypes for {gene} across different populations")
    plt.xlabel("Populations")
    plt.ylabel("Genotype Frequency")
    plt.ylim(0,1)
    plt.legend()
    plt.tight_layout()
    plt.show()
    # --- Console summary ---
    print(f"\nSummary for {gene}:")
    print(f"- Highest AA frequency: {df_gene['AA'].max()} in {df_gene['Population'][df_gene['AA'].idxmax()]}")
    print(f"- Highest Aa frequency: {df_gene['Aa'].max()} in {df_gene['Population'][df_gene['Aa'].idxmax()]}")
    print(f"- Highest aa frequency: {df_gene['aa'].max()} in {df_gene['Population'][df_gene['aa'].idxmax()]}")
    
    gene_interpretations = {
    'ACKR1': 'High aa frequency in Tropical environment reflects strong malaria selection pressure.',
    'SLC24A5': 'High AA frequency in Temperate environment reflects UV-driven pigmentation selection.',
    'EPAS1': 'Variation reflects altitude-based oxygen adaptation across environments.',
    'HBB': 'Sickle cell trait maintained in Tropical environments as malaria resistance.',
    'LCT': 'Lactase persistence higher in populations with pastoral/dairy farming history.',
    'CFTR': 'Cystic fibrosis variant predominantly found in Temperate populations.',
    'MC1R': 'Red hair/freckles variant rare globally, highest in Temperate environments.',
    'TYR': 'Pigmentation variant frequency inversely correlates with UV exposure.',
    'FTO': 'Obesity risk allele shows relatively uniform distribution across environments.',
    'APOE': 'Alzheimers risk allele frequency varies across environmental populations.'
    }

    print(f"- {gene_interpretations.get(gene, 'Population variation reflects environmental selection pressures.')}")

#GRAPH 2
def GenotypeComparisonOfGenes(population, genotype):
    df_population=Sample[Sample["Population"]==population]
    df_genotype=df_population[genotype]
    genes = df_population["Gene"]

    plt.bar(genes, df_genotype)
    plt.xlabel("Genes")
    plt.ylabel("Frequency")
    plt.title(f"Comparison of {genotype} frequency across genes in {population}")
    plt.ylim(0,1)

    for i in range(len(genes)):
        plt.text(i, df_genotype.iloc[i]+0.02,
                 f"{df_genotype.iloc[i]:.3f}", ha='center', fontsize=9)
    plt.tight_layout()
    plt.show()
    # --- Console summary ---
    print(f"\nSummary for {genotype} in {population}:")
    print(f"- Highest {genotype} frequency: {df_population[genotype].max():.3f} in {df_population['Gene'][df_population[genotype].idxmax()]}")
    print(f"- Lowest {genotype} frequency: {df_population[genotype].min():.3f} in {df_population['Gene'][df_population[genotype].idxmin()]}")

    # Dynamic interpretation
    if genotype == "aa":
        print(f"- Genes with high aa frequency in {population} suggest stronger recessive selection pressure in this environment.")
    elif genotype == "AA":
        print(f"- Genes with high AA frequency in {population} suggest dominant allele advantage in this environment.")
    elif genotype == "Aa":
        print(f"- High Aa frequency indicates heterozygote advantage, common in disease resistance genes.")

#GRAPH 3
def AlleleFrequency(gene):
    df_gene=Sample[Sample["Gene"]==gene]

    populations = df_gene["Population"]
    p = df_gene["Allele_A_Freq"]
    q = df_gene["Allele_a_Freq"]

    x = np.arange(len(populations))
    width=0.25

    bar1=plt.bar(x-width, p, width, label="f(A)")
    bar2=plt.bar(x, q, width, label="f(a)")
    plt.title(f"Allelic frequencies of {gene} across different populations")
    plt.xlabel("Populations")
    plt.ylabel("Frequencies")
    
    for i in range(len(populations)):
        plt.text(x[i]-width, p.iloc[i], f"{p.iloc[i]}", ha='center', fontsize=9)
        plt.text(x[i], q.iloc[i], f"{q.iloc[i]}", ha='center', fontsize=9)
    
    plt.legend()
    plt.xticks(x,populations)
    plt.ylim(0,1)
    plt.tight_layout()
    plt.show()
     # --- Console summary ---
    print(f"\nSummary for {gene} allele frequencies:")
    dominant = "A" if df_gene['Allele_A_Freq'].mean() > df_gene['Allele_a_Freq'].mean() else "a"
    print(f"- Allele {dominant} is dominant across populations for {gene}.")
    print(f"- Highest Allele A frequency: {df_gene['Allele_A_Freq'].max():.3f} in {df_gene['Population'][df_gene['Allele_A_Freq'].idxmax()]}")
    print(f"- Highest Allele a frequency: {df_gene['Allele_a_Freq'].max():.3f} in {df_gene['Population'][df_gene['Allele_a_Freq'].idxmax()]}")
    print(f"- Frequency difference reflects environmental selection on {gene}.")


#UI
print("-----------------------------------------")
print("-----------------WELCOME-----------------")  
print("-----------------------------------------")
while True:

    print("WHAT WOULD YOU LIKE TO DO?:")
    print("1. View Sample Data")
    print("2. GENOTYPE FREQUENCIES OF A GENE ACROSS POPULATIONS.")
    print("3. GENOTYPE COMPARISON ACROSS GENES.")
    print("4. ALLELE FREQUENCIES OF A GENE  ACROSS POPULATIONS.")
    ans = input("->(q to quit): ")

    if ans=="1":
        print(Sample)

    elif ans=="2":
        while True:
            print(f"Available Genes: {', '.join(available_genes)}")
            gene1 = input("Which gene?: ").upper()
            if gene1 in available_genes.values:
                GenotypeFrequencyComparisonplot(gene = gene1)  
                break
            else:
                print("This gene does not exist in the database. Please select one from the given options.") 

    elif ans=="3":
        while True:
            print(f"Availabe Populations: {', '.join(available_populations)}")
            population1=input("Which population?:  ")
            print(f"Available genotypes: {', '.join(available_genotypes)}")
            genotype1=input("Which genotype?: ")
            if population1 in available_populations.values and genotype1 in available_genotypes:
                GenotypeComparisonOfGenes(population=population1, genotype=genotype1)
                break
            else:
                print("Either Population or Genotype wrong. Please select from the given options.")

    elif ans=="4":
        while True:
            print(f"Available Genes: {', '.join(available_genes)}")
            gene1=input("Which gene?: ").upper()
            if gene1 in available_genes.values:
                AlleleFrequency(gene=gene1)
                break
            else:
                print("This gene does not exist in the database. Please choose one from the given options.")

    elif ans=="q":
        print("Okay Bye!")
        break

    else:
        print("Invalid input. Please enter 1,2,3 or q.")

