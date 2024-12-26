
# Official Docs
- https://archive.kernel.org/oldwiki/btrfs.wiki.kernel.org/index.php/Main_Page.html => Obsolete Content, still helpful!
- https://btrfs.readthedocs.io/en/latest/index.html => new wiki, however its a BAD copy of the kernel.org (some links/images dont work anymore)
- https://github.com/btrfs/btrfs-dev-docs => developer docs for filesystem internals; last updated 3 years ago...


# Official Repos
- https://github.com/btrfs/linux/tree/master/fs/btrfs
- https://github.com/torvalds/linux/tree/master/fs/btrfs


### Source Code in LINUX Kernel:
- actual file system structure definition:
  - /.../linux$ grep -lrin btrfs --exclude-dir=fs/  | grep btrfs
    ```
    Documentation/filesystems/btrfs.rst
    include/uapi/linux/btrfs.h
    include/uapi/linux/btrfs_tree.h
    include/linux/btrfs.h
    include/trace/events/btrfs.h
    ```
  - LINUX: include/uapi/linux/btrfs_tree.h
    - definition of all the FS-structures


# Helpful Repos

- https://github.com/cblichmann/btrfscue => Recovery tool, rather easy to use => however was not helpful for me
- https://github.com/theY4Kman/btrfs-recon => the repo that started the whole thing!!
- https://github.com/danobi/btrfs-walk => Btrfs in Rust...
  - https://dxuuu.xyz/btrfs-internals.html => basics and superblock
  - https://dxuuu.xyz/btrfs-internals-2.html => Bootstrapping the chunk tree -> sys_chunk_array getting to the respective address
  - https://dxuuu.xyz/btrfs-internals-3.html => Reading the chunk tree -> resolving any objects
  - https://dxuuu.xyz/btrfs-internals-4.html => Reading the root tree root & Reading the filesystem tree root
  - https://dxuuu.xyz/btrfs-internals-5.html => Filesystem tree item types


# Other related topics

### ZFS:
- https://technotes.seastrom.com/assets/2018-11-13-ZFS-reading-list/Aaron_Toponce_ZFS_Administration.pdf

### Btrees:
- https://www.usenix.org/legacy/events/lsf07/tech/rodeh.pdf
- https://raw.githubusercontent.com/klashxx/pdfs/master/B-trees%2C%20Shadowing%2C%20and%20Clones%20(2007).pdf
- https://arxiv.org/pdf/1103.4282v2
