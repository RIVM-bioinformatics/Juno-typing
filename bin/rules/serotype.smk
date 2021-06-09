# ## SEROTYPE ACCORDING TO GENUS ##

# ---------- Choose serotyper and make the multireport accordingly -----------#
def choose_serotyper(wildcards):
    with checkpoints.which_species.get(sample=wildcards.sample).output[0].open() as f:
        species_res = f.read().strip()
        is_salmonella = species_res.find("salmonella") != -1
        is_ecoli = species_res.find("escherichia") != -1
        is_strepto = species_res.find("streptococcus") != -1
        if is_salmonella:
            return OUT+'/serotype/{sample}/SeqSero_result.tsv'
        elif is_ecoli:
            return [OUT + '/serotype/{sample}/data.json',
                    OUT + '/serotype/{sample}/result_serotype.csv']
        elif is_strepto:
            return [OUT + '/serotype/{sample}/pred.tsv']
        else:
            return OUT + "/serotype/{sample}/no_serotype_necessary.txt"

#-----------------------------------------------------------------------------#
# This is just a mock rule to make the multiserotypers work
# Similar to the aggregate samples of https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#data-dependent-conditional-execution
rule aggregate_serotypes:
    input:
        choose_serotyper
    output:
        temp(OUT+'/serotype/{sample}_done.txt')
    threads: 1
    resources: mem_mb=2000
    shell:
        'touch {output}'

#-----------------------------------------------------------------------------#
### Salmonella serotyper ###

rule salmonella_serotyper:
    input:
        r1 = lambda wildcards: SAMPLES[wildcards.sample]["R1"],
        r2 = lambda wildcards: SAMPLES[wildcards.sample]["R2"],
        species = OUT + "/identify_species/{sample}/best_species_hit.txt"
    output:
        OUT+'/serotype/{sample}/SeqSero_result.tsv',
        temp(OUT+'/serotype/{sample}/SeqSero_result.txt'),
        temp(OUT+'/serotype/{sample}/blasted_output.xml'),
        temp(OUT+'/serotype/{sample}/data_log.txt')
    benchmark:
        OUT+'/log/benchmark/serotype_salmonella/{sample}.txt'
    log:
        OUT+'/log/serotype_salmonella/{sample}.log'
    params:
        output_dir = OUT + '/serotype/{sample}/'
    threads: 
        config["threads"]["seqsero2"]
    resources: 
        mem_mb=config["mem_mb"]["seqsero2"]
    conda:
        '../../envs/seqsero.yaml'
    shell:
        """
# Run seqsero2 
# -m 'a' means microassembly mode and -t '2' refers to separated fastq files (no interleaved)
SeqSero2_package.py -m 'a' -t '2' -i {input.r1} {input.r2} -d {params.output_dir} -p {threads}
        """


#-----------------------------------------------------------------------------#
### E. coli serotyper ###

rule ecoli_serotyper:
    input: 
        assembly = lambda wildcards: SAMPLES[wildcards.sample]['assembly'],
        species = OUT + "/identify_species/{sample}/best_species_hit.txt"
    output: 
        json = OUT + '/serotype/{sample}/data.json',
        csv = OUT + '/serotype/{sample}/result_serotype.csv'
    log:
        OUT+'/log/serotype_ecoli/{sample}.log'
    benchmark:
        OUT+'/log/benchmark/serotype_ecoli/{sample}.txt'
    conda: 
        '../../envs/serotypefinder.yaml'
    threads: config["threads"]["serotypefinder"]
    resources: mem_mb=config["mem_mb"]["serotypefinder"]
    params: 
        ecoli_db = config['serotypefinder_db'],
        min_cov = config['serotypefinder']['min_cov'],
        identity_thresh = config['serotypefinder']['identity_thresh'],
        output_dir = OUT + '/serotype/{sample}/'
    shell:
        """
python bin/serotypefinder/serotypefinder.py -i {input.assembly} \
    -o {params.output_dir} \
    -p {params.ecoli_db} \
    -l {params.min_cov} \
    -t {params.identity_thresh} 2> {log}

python bin/serotypefinder/extract_alleles_serotypefinder.py {output.json} {output.csv} 2>> {log}
        """

#-----------------------------------------------------------------------------#
### Streptococcus pneumoniae serotyper ###

rule seroba:
    input:
        r1 = lambda wildcards: SAMPLES[wildcards.sample]["R1"],
        r2 = lambda wildcards: SAMPLES[wildcards.sample]["R2"],
        species = OUT + "/identify_species/{sample}/best_species_hit.txt"
    output:
        OUT + "/serotype/{sample}/pred.tsv"
    log:
        OUT+'/log/serotype_spneumoniae/{sample}.log'
    benchmark:
        OUT+'/log/benchmark/serotype_spneumoniae/{sample}.txt'
    conda:
        "../../envs/seroba.yaml"
    threads: config["threads"]["seroba"]
    resources: mem_mb=config["mem_mb"]["seroba"]
    params:
        min_cov = config["seroba"]["min_cov"],
        seroba_db = config["seroba_db"]
    shell:
        """
rm -rf {wildcards.sample} 
OUTPUT_DIR=$(dirname {output})
mkdir -p $OUTPUT_DIR

seroba runSerotyping --coverage {params.min_cov} {params.seroba_db}/database {input.r1} {input.r2} {wildcards.sample} &> {log}

mv {wildcards.sample}/* $OUTPUT_DIR
        """

#-----------------------------------------------------------------------------#
## No serotyper necessary

rule no_serotyper:
    input: 
        assembly = lambda wildcards: SAMPLES[wildcards.sample]['assembly'],
        species = OUT + "/identify_species/{sample}/best_species_hit.txt"
    output: 
        OUT + "/serotype/{sample}/no_serotype_necessary.txt"
    threads: 1
    resources: mem_mb=1000
    shell:
        """
touch {output}
        """