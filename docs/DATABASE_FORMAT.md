# Database tables

Those items listed here show the structure how the database format corresponds to the btrfs internals.
Please keep in mind, that the database parses the on disk format into a relational structure.
However all links that exist in the database as foreign keys are there because of the relational structure.
All btrfs references do not have a relational structure in the database.

The counts listed here describe how many rows are present in the table.
I had a single disk, and a lot of files and directories and snapshots.

#### General
- address => 36M   # : Address Mapping
- key => 15.7M     # : Holds internal structures

#### Internal Node structure:
- tree_node => 294k    # Called header in BRTFS
- key_ptr => 2.1M      # Internal Node
- leaf_item => 11.4M   # Leaf Node

#### General FS Accounting
- superblock => 2 entries
- dev_item => 2 entries
- sys_chunk => 2
- filesystem => 1 item
- filesystem_device => 1 item
- device => 1 item

#### Internal Chunked Layout of the drive
- chunk_tree => 0
- chunk_item => 3090
- stripe => 3096 entries

#### "values"
- root_item => 3518  => must contain snapshots!!
- dir_item => 2.0M
- inode_item => 1.4M
- file_extent_item => 1.6M
- inode_ref => 1.3M
