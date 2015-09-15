import batch_count7
import batch_count
import time

sam_filename = "/home/christian/packages/HTSeq-0.6.1p1/example_data/yeast_RNASeq_excerpt.sam"
gff_filename = "/home/christian/packages/HTSeq-0.6.1p1/example_data/Saccharomyces_cerevisiae.SGD1.01.56.gtf.gz"
samtype = "sam"
order = "name" 
stranded = "yes"
overlap_mode = "union"
feature_type = "exon"
id_attribute = "gene_id"
quiet = False
minaqual = 10
samout = ""
directory = ""
      
batch_count7.count_reads_in_features(sam_filename, gff_filename, samtype, order,
                            stranded, overlap_mode, feature_type,
                            id_attribute, quiet, minaqual, samout, directory)

start7 = time.time()      
batch_count7.count_reads_in_features(sam_filename, gff_filename, samtype, order,
                            stranded, overlap_mode, feature_type,
                            id_attribute, quiet, minaqual, samout, directory)
final7 = time.time()

start = time.time()      
batch_count.count_reads_in_features(sam_filename, gff_filename, samtype, order,
                            stranded, overlap_mode, feature_type,
                            id_attribute, quiet, minaqual, samout, directory)
final = time.time()

print "Main", final - start
print "7   ", final7 - start7
#print final3 - start3

