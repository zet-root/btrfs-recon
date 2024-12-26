# btrfs-recon

A collection of btrfs on-disk structure parsers, which can feed into a Postgres DB, where they can be changed and written back to disk.

# Corrupted BTRFS

Perform the following steps first:
- make a copy to another filesystem, preferably a filesystem which allows snapshots (ZFS)
- make a snapshot, so you save the original fs dump available
- use the "normal" btrfs tools:
  - [btrfs-check](https://btrfs.readthedocs.io/en/latest/btrfs-check.html) => btrfs tools to repair filesystem
  - [btrfs-rescue](https://btrfs.readthedocs.io/en/latest/btrfs-rescue.html) => btrfs tools to repair filesystem
  - [btrfs-restore](https://btrfs.readthedocs.io/en/latest/btrfs-restore.html) => btrfs tools to repair filesystem
  - [fsck.btrfs](https://btrfs.readthedocs.io/en/latest/fsck.btrfs.html) => btrfs tools to repair filesystem
  - [btrfscue](https://github.com/cblichmann/btrfscue) => Recovery tool, rather easy to use; however was not working for me
- if all of that is not helpful, then use this repository as a last resort

Warning: this is **not simple**!!
- complex setup (database needed, long parsing process)
- manual work required (**you need to know what you do!!!**)
- knowledge of btrfs required!


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
- **db fs scan**: [slow] Actually perform reading all metadata structures:
  - the option "e" defines the byte end of the filesystem, which you get by running the lsblk command

# Analysis: General concept

Btrfs stores its metadata using header blocks prefixed with a unique filesystem UUID, appearing only at specific offsets on the disk.
These properties allow a systematic search across the disk to identify and collect all headers, which is the process outlined in the commands described.

At its core, Btrfs functions like a complex reference tree: certain parts of the filesystem point to other parts necessary for data access.
These reference points are located in known segments of the filesystem, which are accessible when reading from the superblocks.
The superblocks act as the entry point, referencing all other necessary data trees for reading the filesystem.

So, what leads to Btrfs corruption?

Corruption typically occurs when certain references become unreadable, such as pointing to a nonexistent header.
This renders the filesystem unreadable, as the necessary blocks and their locations are lost.
However, Btrfs's design as a copy-on-write filesystem provides a layer of resilience.
This design ensures that data modifications, including deletions, involve writing new blocks rather than overwriting existing ones.
This process retains older versions of data blocks initially, even if they are eventually overwritten.

The recovery process for a corrupted Btrfs involves identifying the last consistent version of the filesystem.
This is feasible given the design of the system and the retention of older data blocks.
Once identified, the most recent consistent tree structure can be restored to the superblocks, complete with accurate checksums.
This recovery method might not restore the most recent data but will recover the last consistent state of the data.

Now comes the hardest part:
- you need to find the issue of your filesystem!!
- that is by far not easy

Some example query what found the issue for my filesystem:

This SQL provides you with possible generation numbers, where a complete tree exists.
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
```

Then you can inspect the tree with the "logical_up" number, which is the logical tree root number.
```
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

In the end I could get my data back by simply running this command:
- the while loop confirms to restore, when asked by the btrfs command
- the btrfs restore works by providing a different root-tree root (which was sufficient for me)
- finally I provide the restore destination and a logfile

```bash
((while true; do echo ""; sleep 1; done) | btrfs restore -s -i -t 3032003772416 /dev/vdb1 /zfswurzel/recover2024/with_snapshots/  2>&1) | tee /zfswurzel/recover2024/some-big-log2-with-snapshots.txt
```

I used ZFS dedup to be able to restore the data of many snapshots all with roughly the same content.
