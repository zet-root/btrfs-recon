# btrfs-recon

A collection of btrfs on-disk structure parsers, which can feed into a Postgres DB, where they can be changed and written back to disk.

# Corrupted BTRFS

Perform the following steps first:
- make a copy to another filesystem, preferably a filesystem which allows snapshots (ZFS)
- make a snapshot, so you save the original fs dump available
- use the "normal" btrfs tools
- if all of that is not helpful, then use this repository as a last resort

Warning:
- this is **not simple**: complex setup (postgres needed)
- manual work required (**you need to know what you do!!!**)

# Usage

## Postgres Setup

```bash
# install
sudo apt install git build-essential postgresql-16 postgresql-server-dev-16
sudo pg_createcluster 16 main --start

# Setup pguint
git clone https://github.com/petere/pguint.git
PGVERSION=16
echo $PGVERSION
export PATH=/usr/lib/postgresql/$PGVERSION/bin:$PATH
cd pguint/
make
sudo make install

# database configuration
sudo -u postgres psql postgres -c "CREATE DATABASE btrfs;"
sudo -u postgres psql btrfs -c "CREATE EXTENSION uint;"
sudo -u postgres psql btrfs -c "CREATE EXTENSION pg_trgm;"
sudo -u postgres psql btrfs -c "CREATE ROLE btrfs_user WITH SUPERUSER LOGIN PASSWORD '[somepassword]';"
sudo -u postgres psql btrfs -c "GRANT ALL ON DATABASE btrfs TO btrfs_user"
```

## Setup

Clone and setup

```bash
snap install astral-uv --classic

git clone https://github.com/zet-root/btrfs-recon.git
cd btrfs-recon
uv sync --extra dev
source .venv/bin/activate
```

Put your database credentials into: btrfs_recon/_config.py
```python
DATABASE_URL: PostgresPsycopgDsn = 'postgresql+psycopg://btrfs_user:[somepassword]@localhost/btrfs'
```

Python needs to access the disk:
- either run as root
- or create a group and give your user access

```bash
sudo groupadd diskaccess
sudo chown root:diskaccess /dev/vda
sudo chmod 660 /dev/vda
sudo usermod -a -G diskaccess yourusername
```

## Example FS

Create an example filesystem, so you test the code and familiarize yourself.

```bash
fdisk /dev/vda
mkfs.btrfs /dev/vda1
mount /dev/vda1 /mnt
btrfs su create /mnt/example-su
btrfs su list /mnt
umount /mnt
```

## Running

Perform all steps to read the metadata into the postgresql database.

```bash
python3 -m btrfs_recon db init
python3 -m btrfs_recon db fs create -l wurzel /dev/vda
python3 -m btrfs_recon db fs sync -l wurzel
lsblk -o +SIZE -b | grep vda1
python3 -m btrfs_recon db fs scan -l wurzel -f --parallel -w 1 -s 0 -e 6442449878528
```

Explanation:
- **db init**: [quick] Initialize all tables in the database
- **db fs create**: [quick] Creates the database structures to know where to read from (just a few inserts)
- **db fs sync**: [quick] Reads the disk layout into the database
- **db fs scan**: [slow] Actually perform reading all metadata structures

# Analysis: General concept

Btrfs stores all of its metadata prefixed by so called header blocks.
These blocks contain the UUID of the filesystem and occur only at specific offsets.
Those two things taken together allow to search through the disk and collect all headers.
This is exactly what the commands above are doing: Searching for all possible headers and storing them in the postgres.

Btrfs is basically a complex reference tree: one part in the filesystem allows you make a lookup at some other part.
Where you have to look, is stored in parts of the filesystem, that you already know.
And if you read the filesystem from scratch, you need to start with the superblocks.
From there all the other lookup trees are referenced and you can start to read data.

So how can a btrfs get corrupted?

Mostly this means that some references are not readable anymore (point to some header, that does not exist).
Therefore the filesystem cannot be read anymore, since we dont know which blocks should be read where (we lost them!!).
However there is hope: btrfs is a copy-on-write filesystem.
That means that whenever we write something new or replace something, we actually write new blocks, instead of overwriting the old ones.
Even a delete is just an operation that removes the references to the old blocks.
Of course at some point the filesystem overwrites old blocks, but initially the old versions are still there.
That also means, that there are MUCH more blocks with their headers, that we can find on disk, which are not used anymore.
So the task in recoving a corrupted btrfs becomes a task of: What is the last consistent verion?
Once you have found that (and the likelyhood is rather high) you can simply put the tree-top into the superblocks (together with their correct checksums).
If this was the only issue, then you should be able to get your data back. Not the lastest data, but the data available at this last-correct version.


Now comes the hardest part:
- you need to find the issue of your filesystem!!
- that is by far not easy

Some example query what found the issue for my filesystem:

```sql
WITH complete_tree AS (
    SELECT DISTINCT a.bytenr AS logical_up, kp.blockptr AS logical_down, tn."level" AS lvl, tn.generation
    FROM key_ptr kp
    JOIN tree_node tn ON (kp.parent_id = tn.id)
    JOIN address a ON (tn.address_id = a.id)
)

SELECT *
FROM (
    SELECT DISTINCT a.bytenr AS logical, tn.generation
    FROM tree_node tn
    JOIN address a ON (tn.address_id = a.id)
    JOIN leaf_item li ON (tn.id = li.parent_id)
    JOIN KEY k ON (li.key_id = k.id)
    WHERE tn."level" = 0 AND k.ty = 'RootItem'
) AS leaf_nodes
JOIN complete_tree AS ct1 ON (leaf_nodes.logical = ct1.logical_down AND ct1.lvl = 1 AND ct1.generation >= leaf_nodes.generation)
--  JOIN complete_tree AS ct2 ON (ct1.logical_up = ct2.logical_down AND ct2.lvl = 2 AND ct2.generation >= ct1.generation)
--  LEFT JOIN complete_tree AS ct3 ON (ct2.logical_up = ct3.logical_down AND ct3.lvl = 3 AND ct3.generation >= ct2.generation)
ORDER BY ct1.generation desc



WITH complete_tree AS (
    SELECT DISTINCT a.bytenr AS logical_up, kp.blockptr AS logical_down, tn."level" AS lvl, tn.generation
    FROM key_ptr kp
    JOIN tree_node tn ON (kp.parent_id = tn.id)
    JOIN address a ON (tn.address_id = a.id)
)

SELECT distinct k.objectid, k.ty, k."offset", k.struct_type
FROM tree_node tn
JOIN address a ON (tn.address_id = a.id)
JOIN leaf_item li ON (tn.id = li.parent_id)
JOIN KEY k ON (li.key_id = k.id)
JOIN complete_tree AS ct1 ON (a.bytenr = ct1.logical_down AND ct1.lvl = 1 AND ct1.generation >= tn.generation)
WHERE ct1.logical_up = 3032003772416
```
