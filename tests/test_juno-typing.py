import base_juno_pipeline
import csv
import os
import pathlib
from sys import path
import unittest

main_script_path = str(pathlib.Path(pathlib.Path(__file__).parent.absolute()).parent.absolute())
path.insert(0, main_script_path)
from bin import download_dbs
import juno_typing



@unittest.skipIf(not pathlib.Path('/mnt/scratch_dir/hernanda').exists(),
                    "Skipped in non-RIVM environments (for sake of time)")
class TestDownloadDbs(unittest.TestCase):
    """Testing the downloading of databases and software used by the pipeline"""

    def setUpClass():
        pathlib.Path('fake_db').mkdir(exist_ok = True)

    def tearDownClass():
        os.system('rm -rf fake_db')

    def test_download_all_dbs(self):
        """Testing all databases/software are downloaded and set up"""

        path_to_db = pathlib.Path('fake_db')
        path_to_bin = pathlib.Path('bin')
        downloads = download_dbs.DownloadsJunoTyping(path_to_db, 
                                                    update_dbs=True,
                                                    cge_mlst_asked_version='2.0.4',
                                                    mlst7_db_asked_version='master',
                                                    serotypefinder_db_asked_version='master',
                                                    seroba_db_asked_version='master',
                                                    seroba_kmersize=50)
        self.assertEqual(downloads.seroba_kmersize, 50)
        self.assertEqual(downloads.downloaded_versions['mlst7'], '2.0.4')
        self.assertTrue(path_to_bin.joinpath('cge-mlst', 'mlst.py').exists())
        self.assertTrue(path_to_db.joinpath('mlst7_db', 'senterica', 'senterica.length.b').exists())
        self.assertTrue(path_to_db.joinpath('serotypefinder_db', 'H_type.seq.b').exists())
        self.assertTrue(path_to_db.joinpath('seroba_db', 'database', 'cdhit_cluster').exists())



class TestJunoTypingDryRun(unittest.TestCase):
    """Testing the JunoTyping class (code specific for this pipeline)"""

    def setUpClass():
        fake_dirs = ['fake_dir_wsamples', 
                    'fake_dir_juno', 
                    'fake_dir_juno/clean_fastq', 
                    'fake_dir_juno/de_novo_assembly_filtered',
                    'fake_db',
                    'fake_db/mlst7_db/',
                    'fake_db/mlst7_db/senterica/']

        fake_files = ['fake_dir_wsamples/sample1_R1.fastq',
                    'fake_dir_wsamples/sample1_R2.fastq.gz',
                    'fake_dir_wsamples/sample2_R1_filt.fq',
                    'fake_dir_wsamples/sample2_R2_filt.fq.gz', 
                    'fake_dir_wsamples/sample1.fasta',
                    'fake_dir_wsamples/sample2.fasta',
                    'fake_dir_juno/clean_fastq/1234_R1.fastq.gz',
                    'fake_dir_juno/clean_fastq/1234_R2.fastq.gz', 
                    'fake_dir_juno/de_novo_assembly_filtered/1234.fasta',
                    'fake_db/mlst7_db/senterica/senterica.length.b']
                            
        for folder in fake_dirs:
            pathlib.Path(folder).mkdir(exist_ok = True)
        for file_ in fake_files:
            with open(file_, mode='w') as metadata_file:
                metadata_writer = csv.writer(metadata_file, 
                                            delimiter=',', 
                                            quotechar='"',
                                            quoting=csv.QUOTE_MINIMAL)
                metadata_writer.writerow(['content1'])
                metadata_writer.writerow(['content2'])

        with open('fake_dir_wsamples/fake_metadata.csv', mode='w') as metadata_file:
            metadata_writer = csv.writer(metadata_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            metadata_writer.writerow(['sample', 'genus', 'species'])
            metadata_writer.writerow(['sample1', 'Salmonella', 'enterica'])
            metadata_writer.writerow(['sample2', 'Escherichia', 'coli'])


    def tearDownClass():
        fake_dirs = ['fake_dir_wsamples', 
                    'fake_dir_juno', 
                    'fake_db',
                    'test_output']
        for folder in fake_dirs:
            os.system('rm -rf {}'.format(str(folder)))
    
    def test_junotyping_dryrun(self):
        """Testing the pipeline runs properly as a dry run"""
        juno_typing_run = juno_typing.JunoTypingRun(input_dir = 'fake_dir_wsamples', 
                                                    metadata = None,
                                                    species = 'Salmonella enterica',
                                                    output_dir = pathlib.Path('test_output'), 
                                                    db_dir = pathlib.Path('fake_db'),
                                                    dryrun = True)
        self.assertTrue(juno_typing_run.successful_run, 'Exception raised when running a dryrun')

    def test_junotyping_dryrun_wMetadata(self):
        """Testing the pipeline runs properly as a dry run when providing a metadata file"""
        juno_typing_run = juno_typing.JunoTypingRun(input_dir = 'fake_dir_wsamples', 
                                                    metadata= 'fake_dir_wsamples/fake_metadata.csv',
                                                    output_dir = pathlib.Path('test_output'), 
                                                    db_dir = pathlib.Path('fake_db'),
                                                    dryrun = True)
        self.assertTrue(juno_typing_run.successful_run, 'Exception raised when running a dryrun and providing a metadata file')



@unittest.skipIf(not pathlib.Path('/data/BioGrid/hernanda/test_data_per_pipeline/Enteric/Juno-typing/').exists(),
                    "Skipped in non-RIVM environments (because test data is needed)")
class TestJunoTypingPipeline(unittest.TestCase):
    """Testing the JunoTyping class (code specific for this pipeline)"""

    def setUpClass():
        os.system('rm -rf test_output')

    def tearDownClass():
        os.system('rm -rf test_output')
    
    def test_junotyping_run(self):
        """Testing the pipeline runs properly with real samples"""
        output_dir = pathlib.Path('test_output')
        juno_typing_run = juno_typing.JunoTypingRun(input_dir = '/data/BioGrid/hernanda/test_data_per_pipeline/Enteric/Juno-typing/', 
                                    db_dir = '/mnt/db/juno/typing_db',
                                    output_dir = output_dir)
        self.assertTrue(juno_typing_run.successful_run, 'Exception raised when running a dryrun')
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport.csv').exists())
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport1.csv').exists())
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport2.csv').exists())
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport3.csv').exists())
        self.assertTrue(output_dir.joinpath('mlst7', 'mlst7_multireport.csv').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'log_git.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'log_pipeline.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'log_conda.txt').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'juno_typing_report.html').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'sample_sheet.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'user_parameters.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'database_versions.yaml').exists())

    def test_junotyping_run_wMetadata(self):
        """Testing the pipeline runs properly with real samples when providing a metadata file"""
        output_dir = pathlib.Path('test_output')
        pipeline_run = juno_typing.JunoTypingRun(input_dir = '/data/BioGrid/hernanda/test_data_per_pipeline/Enteric/Juno-typing/', 
                                    db_dir = '/mnt/db/juno/typing_db',
                                    metadata= '/data/BioGrid/hernanda/test_data_per_pipeline/Enteric/Juno-typing/metadata.csv',
                                    output_dir = output_dir)
        self.assertTrue(pipeline_run.successful_run, 'Exception raised when running a dryrun')
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport.csv').exists())
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport1.csv').exists())
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport2.csv').exists())
        self.assertTrue(output_dir.joinpath('serotype', 'serotyper_multireport3.csv').exists())
        self.assertTrue(output_dir.joinpath('mlst7', 'mlst7_multireport.csv').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'log_git.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'log_pipeline.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'log_conda.txt').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'juno_typing_report.html').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'sample_sheet.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'user_parameters.yaml').exists())
        self.assertTrue(output_dir.joinpath('audit_trail', 'database_versions.yaml').exists())


if __name__ == '__main__':
	unittest.main()