"""
Created on Jan 26, 2017

@author: Siyuan Qi

This file visualizes the affordance stats collected from SUNCG.

"""

# System imports
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches
import matplotlib.collections
import scipy.stats
import scipy.ndimage
import PIL

import config


# ============================= Plot Affordance Stats =============================
def filter_afforance(aff):
    distance_limit = 2
    aff_filter = np.logical_and(np.abs(aff[:, 0]) < distance_limit, np.abs(aff[:, 1]) < distance_limit)
    return aff[aff_filter, :]


def plot_affordance(paths):
    matplotlib.rcParams.update({'font.size': 22})
    with open(os.path.join(paths.metadata_root, 'stats', 'furnitureAffordance.json')) as f:
        affordance_stats = json.load(f)

    plot_folder = os.path.join(paths.tmp_root, 'affordance_plot')
    if not os.path.exists(plot_folder):
        os.makedirs(plot_folder)

    for furniture, affordance_list in affordance_stats.items():
        print furniture
        aff = filter_afforance(np.array(affordance_list))
        heatmap, xedges, yedges = np.histogram2d(aff[:, 0], aff[:, 1], bins=[20, 20], range=[[-2, 2], [-2, 2]])
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

        # For better visualization
        new_size = 200
        im = PIL.Image.fromarray(heatmap)
        im = im.resize((new_size, new_size), PIL.Image.ANTIALIAS)
        im = np.array(list(im.getdata()))
        heatmap = im.reshape((new_size, new_size))
        # heatmap = scipy.ndimage.gaussian_filter(heatmap, sigma=(5, 5))

        fig = plt.figure()
        plt.clf()
        plt.imshow(heatmap.T, extent=extent, origin='lower')
        plt.xticks(np.arange(-2, 3, 1.0))
        plt.yticks(np.arange(-2, 3, 1.0))
        plt.savefig(os.path.join(plot_folder, furniture + '.png'), bbox_inches='tight')
        plt.close(fig)


# ============================= Plot Planning Results =============================
def plot_furniture(furniture, ax, name=""):
    rectangle = np.array(furniture)
    center = np.mean(rectangle, axis=0)
    plt.text(center[0], center[1], name)
    rectangle = np.vstack((rectangle, rectangle[0, :]))
    polygon = matplotlib.patches.Polygon(rectangle, fill=True, zorder=2, facecolor='slategray', edgecolor='k')
    ax.add_patch(polygon)


def plot_planning_heatmaps(paths):
    plot_folder = os.path.join(paths.tmp_root, 'heatmaps', 'figures')
    if not os.path.exists(plot_folder):
        os.makedirs(plot_folder)

    for house_room_id_json in os.listdir(os.path.join(paths.tmp_root, 'heatmaps')):
        print house_room_id_json
        if not os.path.isdir(os.path.join(paths.tmp_root, 'heatmaps', house_room_id_json)):
            with open(os.path.join(paths.tmp_root, 'heatmaps', house_room_id_json)) as f:
                heatmap_info = json.load(f)
            house_room_id = os.path.splitext(house_room_id_json)[0]

            roomSize = heatmap_info.get('roomSize')
            furnitures = heatmap_info.get('furnitures')
            trajectories = heatmap_info.get('trajectories')

            map_scale = 100
            interpolation = 100
            start_end_cut = 5

            # ==================== Plot trajectories ====================
            fig = plt.figure()
            room_map = np.zeros((int(roomSize[0]*map_scale), int(roomSize[1]*map_scale)))
            plt.imshow(room_map.T, origin='lower')

            ax = plt.gca()

            if furnitures:
                for furniture in furnitures:
                    furniture = np.array(furniture)*map_scale
                    plot_furniture(furniture, ax)

            ax.autoscale(False)
            if trajectories:
                for trajectory in trajectories:
                    if not trajectory:
                        continue
                    trajectory = np.array(trajectory)*map_scale
                    plt.plot(trajectory[:, 0], trajectory[:, 1], zorder=1, color='w')

            ax.set_xticklabels([])
            ax.set_yticklabels([])
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(os.path.join(plot_folder, house_room_id + '_trajectries.png'), bbox_inches='tight', pad_inches=0)
            plt.close(fig)

            # ==================== Plot heatmap ====================
            fig = plt.figure()
            ax = plt.gca()

            heatmap = np.zeros((int(roomSize[0]*map_scale), int(roomSize[1]*map_scale)))

            if trajectories:
                for i_traj in range(len(trajectories)):
                    if not trajectories[i_traj]:
                        continue
                    trajectory = np.array(trajectories[i_traj])*map_scale
                    for i in range(trajectory.shape[0]-start_end_cut):
                        if i < start_end_cut:
                            continue

                        x = trajectory[i, 0]
                        y = trajectory[i, 1]
                        dx = (trajectory[i+1, 0] - trajectory[i, 0])/interpolation
                        dy = (trajectory[i+1, 1] - trajectory[i, 1])/interpolation
                        for inter in range(interpolation):
                            x += dx
                            y += dy
                            heatmap[int(x), int(y)] += 1

            heatmap = scipy.ndimage.grey_dilation(heatmap, size=(3, 3))
            heatmap = scipy.ndimage.gaussian_filter(heatmap, sigma=(5, 5))
            plt.imshow(heatmap.T, origin='lower')

            if furnitures:
                for furniture in furnitures:
                    furniture = np.array(furniture)*map_scale
                    plot_furniture(furniture, ax)

            ax.set_xticklabels([])
            ax.set_yticklabels([])
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(os.path.join(plot_folder, house_room_id + '_heatmap.png'), bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            # break


# ============================= Plot Sampling Results =============================
def plot_sample(paths):
    for room_type in os.listdir(os.path.join(paths.tmp_root, 'samples')):
        sample_folder = os.path.join(paths.tmp_root, 'samples', room_type, 'json')
        plot_folder = os.path.join(paths.tmp_root, 'figures', room_type)
        # plot_folder = os.path.join(paths.tmp_root, 'samples', room_type, 'figures')
        if not os.path.exists(plot_folder):
            os.makedirs(plot_folder)
        if not os.path.exists(os.path.join(plot_folder, 'transparent')):
            os.makedirs(os.path.join(plot_folder, 'transparent'))

        for sample_json in sorted(os.listdir(sample_folder)):
            print sample_json

            if not os.path.isdir(os.path.join(sample_folder, sample_json)):
                with open(os.path.join(sample_folder, sample_json)) as f:
                    sample_room = json.load(f)
                sample_id = os.path.splitext(sample_json)[0]

                roomSize = sample_room.get('roomSize')
                furnitures = sample_room.get('furnitures')
                affordance = sample_room.get('affordance')

                fig = plt.figure()
                ax = plt.gca()
                ax.add_patch(matplotlib.patches.Rectangle((0, 0), roomSize[0], roomSize[2], linewidth=5, fill=False, zorder=1))

                if furnitures:
                    for furnitureName, furniture_vertices in furnitures.items():
                        for rectange in furniture_vertices:
                            rectange = np.array(rectange)
                            plot_furniture(rectange[:, [0, 2]], ax, furnitureName)

                # if affordance:
                #     for furnitureName, affordance_pos in affordance.items():
                #         print furnitureName
                #         affordance_pos = np.array(affordance_pos)
                #         # plt.scatter(affordance_pos[:, 0], affordance_pos[:, 2])

                ax.set_xlim([0, roomSize[0]])
                ax.set_ylim([0, roomSize[2]])
                ax.axes.xaxis.set_ticklabels([])
                ax.axes.yaxis.set_ticklabels([])
                ax.tick_params(axis=u'both', which=u'both', length=0)
                ax.set_aspect('equal', adjustable='box')
                # plt.show()
                fig_name = os.path.join(plot_folder, sample_id + '.png')
                plt.savefig(fig_name)
                plt.close(fig)
                # os.system('convert {} -transparent white {}'.format(fig_name, os.path.join(plot_folder, 'transparent', sample_id + '.png')))


def main():
    paths = config.Paths()
    # plot_affordance(paths)
    # plot_planning_heatmaps(paths)
    plot_sample(paths)


if __name__ == '__main__':
    main()
