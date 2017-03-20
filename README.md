# MGFproper
MGF cleanup for MS library search approach: select spectra on specific fragments and annotate using Mascot XML data

For more information see:

W. Fremout, M. Dhaenens, S. Saverwyns, J. Sanyova, P. Vandenabeele, D. Deforce, L. Moens, Development of a dedicated peptide tandem mass spectral library for conservation science, Analytica Chimica Acta. 728 (2012) 39–48. doi:10.1016/j.aca.2012.03.037.
http://www.sciencedirect.com/science/article/pii/S0003267012004540


'''
MGF proper - MGF cleanup for MS library search approach: select spectra on specific fragments and annotate using Mascot XML data
  Author:       Wim Fremout / Royal Institute for Cultural Heritage, Brussels, Belgium (18 Nov 2011)
  Licence:      GNU GPL version 3.0

Usage: mgfproper.py [options] ORIGINAL_MGF

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -s SAMPLE, --sample=SAMPLE
                        sample name (default: base name of the original MGF
                        file)
  -d DESC, --desc=DESC  long sample description, use "
  -v, --verbose         be very verbose

  Mass tag selection of spectra:
    --tags=TAGS         tags in comma separated list in Da (default:
                        147.1,175.1)
    --error=ERROR       mass error in Da (default: 0.5)
    --limit=LIMIT       minimal height the mass tag peak, either as a non-
                        normalised absolute value or as a percentage (default:
                        5%)
    --onetag            remove spectra having more than one tag
    --notags            no mass tag based selection of spectra

  Mascot annotation using XML file:
    --mascot=XMLFILE    use specified XML file (default: same base name as the
                        original MGF file)
    --bold              annotation requires bold (-> first appearance)
    --red               annotation requires red (-> highest rank)
    --score=SCORE       annotation requires a minimum score (default: 40)
    --nomascot          no mascot annotation
'''