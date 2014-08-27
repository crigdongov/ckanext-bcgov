import logging
import pprint

import ckan.plugins as p
import ckan.logic as logic
import ckan.model as model

import ckan.plugins.toolkit as toolkit
from ckan.common import  c
from ckanext.hierarchy.model import GroupTreeNode
from ckanext.edc_schema.util.helpers import org_record_is_viewable 


log = logging.getLogger(__name__)
_get_or_bust = logic.get_or_bust


@logic.side_effect_free
def group_tree(context, data_dict):
    '''Returns the full group tree hierarchy.

    :returns: list of top-level GroupTreeNodes
    '''
    model = _get_or_bust(context, 'model')
    group_type = data_dict.get('type', 'group')
    top_level_groups = data_dict['top_groups']
    pkg_count = data_dict['pkg_count']
    return [_group_tree_branch(group, pkg_count, type=group_type) for group in top_level_groups]

    
    #    return [_group_tree_branch(group, type=group_type)
#            for group in model.Group.get_top_level_groups(type=group_type)]


@logic.side_effect_free
def group_tree_section(context, data_dict):
    '''Returns the section of the group tree hierarchy which includes the given
    group, from the top-level group downwards.

    :param id: the id or name of the group to inclue in the tree
    :returns: the top GroupTreeNode of the tree section
    '''
    group_name_or_id = _get_or_bust(data_dict, 'id')
    model = _get_or_bust(context, 'model')
    group = model.Group.get(group_name_or_id)
    
    pkg_count = data_dict['pkg_count']
    
    if group is None:
        raise p.toolkit.ObjectNotFound
    group_type = data_dict.get('type', 'group')
    if group.type != group_type:
        how_type_was_set = 'was specified' if data_dict.get('type') \
                           else 'is filtered by default'
        raise p.toolkit.ValidationError(
            'Group type is "%s" not "%s" that %s' %
            (group.type, group_type, how_type_was_set))
    root_group = (group.get_parent_group_hierarchy(type=group_type) or [group])[0]
    return _group_tree_branch(root_group, pkg_count, highlight_group_name=group.name,
                              type=group_type)




def count_user_packages(group_id):
    '''Counts the number of packages a user has access to in an organization
    '''
    count = 0
    
    group_packages = toolkit.get_action('group_package_show')(data_dict={'id': group_id})
    
    for package in group_packages:
        
        if org_record_is_viewable( package, c.userobj):
            count += 1

    return count
    
    
def _group_tree_branch(root_group, pkg_count, highlight_group_name=None, type='group'):
    '''Returns a branch of the group tree hierarchy, rooted in the given group.

    :param root_group_id: group object at the top of the part of the tree
    :param highlight_group_name: group name that is to be flagged 'highlighted'
    :returns: the top GroupTreeNode of the tree
    '''
    import pprint
    nodes = {}  # group_id: GroupTreeNode()

    #Calculate package count for root orgs
    root_count = pkg_count[root_group.id]
    #root_count = count_user_packages(root_group.id)
    for group_id, group_name, group_title, parent_id in root_group.get_children_group_hierarchy(type=type):
        if group_id in pkg_count :
            root_count += pkg_count[group_id]
            #root_count = count_user_packages(group_id)
             
    root_node = nodes[root_group.id] = GroupTreeNode(
        {'id': root_group.id,
         'pkg_num': str(root_count),
         'name': root_group.name,
         'title': root_group.title,
         'is_top_org' : True})
    if root_group.name == highlight_group_name:
        nodes[root_group.id].highlight()
        highlight_group_name = None
    for group_id, group_name, group_title, parent_id in \
            root_group.get_children_group_hierarchy(type=type):
        if group_id in pkg_count :
            pkg_num = pkg_count[group_id]
            #pkg_num = count_user_packages(group_id)
            #pprint.pprint(pkg_num)
        else :
            pkg_num = 0

        #        pkg_num = pkg_count[group_id]
        node = GroupTreeNode({'id': group_id,
                             'pkg_num': str(pkg_num),
                              'name': group_name,
                              'title': group_title,
                              'is_top_org' : False})
        nodes[parent_id].add_child_node(node)
        if highlight_group_name and group_name == highlight_group_name:
            node.highlight()
        nodes[group_id] = node
    return root_node