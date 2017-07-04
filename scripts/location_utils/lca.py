# O(n) solution to find LCS of two given values n1 and n2

# A binary tree node
class Node:
    # Constructor to create a new binary node
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


# Finds the path from root node to given root of the tree.
# Stores the path in a list path[], returns true if path
# exists otherwise false
def findPath(root, path, k):
    # Baes Case
    if root is None:
        return False

    # Store this node is path vector. The node will be
    # removed if not in path from root to k
    path.append(root.key)

    # See if the k is same as root's key
    if root.key == k:
        return True

    # Check if k is found in left or right sub-tree
    if ((root.left != None and findPath(root.left, path, k)) or
            (root.right != None and findPath(root.right, path, k))):
        return True

    # If not present in subtree rooted with root, remove
    # root from path and return False

    path.pop()
    return False


# find path from key1 to key2
def findNode(root, key):
    if root is None:
        return None

    if root.key == key:
        return root

    node = None
    if not root.left is None:
        node = findNode(root.left, key)

    if not node is None:
        return node

    if not root.right is None:
        node = findNode(root.right, key)

    return node



# Returns LCA if node n1 , n2 are present in the given
# binary tre otherwise return -1
def findLCA(root, n1, n2):
    # To store paths to n1 and n2 fromthe root
    path1 = []
    path2 = []

    # Find paths from root to n1 and root to n2.
    # If either n1 or n2 is not present , return -1
    if (not findPath(root, path1, n1) or not findPath(root, path2, n2)):
        return -1

    # Compare the paths to get the first different value
    i = 0
    while (i < len(path1) and i < len(path2)):
        if path1[i] != path2[i]:
            break
        i += 1
    return path1[i - 1]


def regional_hierarchy():
    root = Node(13)
    root.left = Node(14)
    root.right = Node(20)
    root.left.left = Node(2)
    root.left.right = Node(1)

    v20 = root.right
    v20.left = Node(17)
    v20.right = Node(23)

    v17 = v20.left
    v17.left = Node(16)
    v17.right = Node(19)

    v16 = v17.left
    v16.left = Node(5)
    v16.right = Node(15)
    v16.right.left = Node(4)
    v16.right.right = Node(3)

    v19 = v17.right
    v19.left = Node(8)
    v19.right = Node(18)
    v19.right.left = Node(6)
    v19.right.right = Node(7)

    v23 = v20.right
    v23.left = Node(9)
    v23.right = Node(22)

    v22 = v23.right
    v22.left = Node(10)
    v22.right = Node(21)
    v22.right.left = Node(12)
    v22.right.right = Node(11)

    return root
