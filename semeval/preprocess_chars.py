from Tweet import *
from util import normalize_tweet
from util.sentic_grabber import getSentics
import copy
from collections import defaultdict
import cPickle
import re
import codecs
import argparse


URL_PATTERN = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
USER_PATTERN = re.compile(ur'@\w+')
NUM_PATTERN = re.compile(ur'[0-9]+')
PUNCT_PATTERN = re.compile(ur'\W{4,}')
PATTERNS = {
    'URL': URL_PATTERN,
    'USER': USER_PATTERN,
    'NUM': NUM_PATTERN
}


class Line(object):
    def __init__(self, raw, line_no):
        parts = raw.split(',')
        self.line_no = line_no
        self.tid = None
        self.txt = None
        self.chars = None
        self.label = None
        self.error = False
        if len(parts) != 6:
            bad_parts = parts[5:]
            new_str = ', '.join(bad_parts)
            parts = parts[:5] + [new_str]
        if len(parts) != 6:
            print('parsing: bad line @ %d (parts len = %d): %s' % (self.line_no, len(parts), raw))
            # print(parts)
            self.error = True
        else:
            self.tid = parts[1].strip('"')
            self.txt = parts[5].strip('"')
            self.label = int(parts[0].strip('"'))
        self.tokens = None

    def __repr__(self):
        if self.txt is not None:
            return 'Line(%s)' % self.txt
        else:
            return 'Line(ERROR)'


def charify(line):
    text = line.txt
    if text is not None:
        prechars, mapping = normalize_tweet(text)
        chars = list(prechars)
        line.chars = chars
        return chars, mapping
    else:
        return None


def process(filename, dictionary=None, ascii=False):
    print('processing %s' % filename)
    unicode_errors = 0
    parse_errors = 0
    lines = []
    count = 0
    mode = 'utf-8'
    if ascii:
        mode = 'ascii'
    with codecs.open(filename, 'rU', mode, 'ignore') as f:
        for line in f:
            parsed = Line(line.rstrip('\n'), count)
            if parsed.error:
                parse_errors += 1
            else:
                lines.append(parsed)
            count += 1
    print('%d / %d lines with unicode errors' % (unicode_errors, count))
    print('%d / %d lines with parse errors' % (parse_errors, count))

    make_dict = False
    if dictionary is None:
        dictionary = {}
        make_dict = True

    print('make dictionary? %s' % make_dict)

    nlines = len(lines)
    ncomplete = 0
    processed_lines = []
    count = 0
    for line in lines:
        chars, mapping = charify(line)
        if chars is not None:
            processed_lines.append(line)
            if make_dict:
                for c in chars:
                    if c not in dictionary:
                        dictionary[c] = count
                        count += 1
            ncomplete += 1
        if (ncomplete % 10000) == 0:
            print('%d / %d' % (ncomplete, nlines))
    return processed_lines, dictionary, mapping


def write(outfile, lines, dictionary, mapping, write_dict=False, label_map=None, ascii=False):
    print('writing %s' % outfile)
    if write_dict:
        dict_filename = '%s.vocab.pkl' % outfile
        print('writing dictionary to %s' % dict_filename)
        cPickle.dump(dictionary, open(dict_filename, 'w'))
    mode = 'utf-8'
    if ascii:
        mode = 'ascii'
    outf = codecs.open(outfile, 'w+', mode)
    assert label_map is not None
    int2label = {0: "negative", 2: "neutral", 4: "positive"}
    npos = 0
    nneg = 0
    nskips = 0
    for line in lines:
        if int2label[int(line.label)] == 'neutral':
            continue
        if line.txt is None or line.chars is None:
            nskips += 1
        else:
            ints = []
            sentics = []
            for c,word in zip(line.chars, mapping):
                if c in dictionary:
                    ints.append(str(dictionary[c]))
                    sentics.append(str(getSentics(word)))
            text = ' '.join(ints)
            senticText = '|'.join(sentics)
            if line.label not in label_map:
                assert int(line.label) in int2label, 'bad label? %s' % line.label
                label_str = int2label[int(line.label)]
                label = label_map[label_str]
            else:
                label = label_map[line.label]
            if label == 0:
                npos += 1
            else:
                nneg += 1
            outline = '%s\t%s\t%s\n' % (str(label), text, senticText)
            outf.write(outline)
    print('skipped %d lines' % nskips)
    print 'npos: %d, nneg: %d' % (npos, nneg)


def main(args):
    filename = args.tweet_file
    label_map = cPickle.load(open(args.label_map, 'r'))
    print(label_map)
    lines, dictionary, mapping = process(filename, ascii=args.ascii)
    print('dict:')
    print(dictionary)
    outfile = args.output_file
    write(outfile, lines, dictionary, mapping, write_dict=True, label_map=label_map, ascii=args.ascii)
    if args.test_file:
        testfile = args.test_file
        print('processing test file %s' % testfile)
        lines, _, _ = process(testfile, dictionary=dictionary, ascii=args.ascii)
        write(outfile + '.test', lines, dictionary, mapping, write_dict=False, label_map=label_map, ascii=args.ascii)
    print('done')


def main_semeval(args):
    trainfile = args.tweet_file
    label_map = cPickle.load(open(args.label_map, 'r'))

    assert args.output_dir is not None
    outdir = args.output_dir

    vocab = None
    if args.vocab_file:
        vocab_file = args.vocab_file
        vocab = cPickle.load(open(vocab_file, 'r'))

    train_out = '%s/train.chars.tsv' % outdir
    preprocess_semeval(trainfile, train_out, vocab=vocab, label_dict=label_map)

    if args.dev_file:
        dev_out = '%s/dev.chars.tsv' % outdir
        preprocess_semeval(args.dev_file, dev_out, vocab=vocab, label_dict=label_map)

    if args.test_file:
        test_out = '%s/test.chars.tsv' % outdir
        preprocess_semeval(args.test_file, test_out, vocab=vocab, label_dict=label_map)


def preprocess_semeval(infile, outfile, vocab=None, label_dict=None):
    tweets = load_from_tsv(infile, subtask_id='a')
    tweets = filter(lambda t: t.label != 'neutral', tweets)
    print('loaded %d tweets from %s' % (len(tweets), infile))
    texts = map(lambda t: t.raw_text, tweets)
    labels = map(lambda t: t.label, tweets)
    mk_label_map = False
    if label_dict is None:
        mk_label_map = True
        label_set = list(set(labels))
        label_dict = {x: label_set.index(x) for x in label_set}
    label_ints = map(lambda t: label_dict[t.label], tweets)
    mk_vocab = False
    if vocab is None:
        mk_vocab = True
        vocab = defaultdict(int)
    else: print "Using preloaded vocab"
    ntexts = []
    nSentics = []
    ct = 0
    for text in texts:
        ntext, mapping = normalize_tweet(text)
        ntexts.append(ntext)
        nSentic = [getSentics(word) for word in mapping]
        nSentics.append(nSentic)
        if mk_vocab:
            chars = list(ntext)
            for c in chars:
                if c not in vocab:
                    vocab[c] = ct
                    ct += 1
    print(vocab)
    print
    lines = []
    for i, (text, sentic) in enumerate(zip(ntexts, nSentics)):
        ints = map(lambda c: vocab[c], text)
        ints_str = ' '.join([str(c) for c in ints])
        sentics_str = '|'.join([str(tup) for tup in sentic])
        label = str(label_ints[i])
        line = label + "\t" + ints_str + "\t" + sentics_str
        lines.append(line)

    if mk_vocab:
        vocab_filename = '%s.vocab.pkl' % outfile
        print('writing vocab to %s' % vocab_filename)
        cPickle.dump(vocab, open(vocab_filename, 'w'))
    if mk_label_map:
        label_filename = '%s.labels.pkl' % outfile
        print('writing label map to %s' % label_filename)
        cPickle.dump(label_dict, open(label_filename, 'w'))

    print('writing output to %s' % outfile)
    with open(outfile, 'w') as f:
        for line in lines:
            f.write(line + '\n')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Process 1.6M tweet corpus")
    parser.add_argument('--output-file', help="location, name of output")
    parser.add_argument('--output-dir', help='dir for output')

    parser.add_argument('--tweet-file', help="location of 1.6M corpus", required=True)
    parser.add_argument('--label-map', help='label map', required=True)

    parser.add_argument('--test-file', help="location of test file", default=None)
    parser.add_argument('--dev-file', help="location of test file", default=None)

    parser.add_argument('--vocab-file', help='vocab')
    parser.add_argument('--ascii', type=bool, default=False)
    parser.add_argument('--semeval', type=bool, default=False)

    args = parser.parse_args()
    print("ARGS:")
    print(args)
    if args.semeval:
        main_semeval(args)
    else:
        main(args)

