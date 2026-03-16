import sys
import random
import numpy as np
import xml.etree.ElementTree as ET
from mujoco_env.mujoco_parser import MuJoCoParserClass
from mujoco_env.utils import prettify, sample_xyzs, rotation_matrix, add_title_to_img
from mujoco_env.ik import solve_ik
from mujoco_env.transforms import rpy2r, r2rpy
import os
import copy
import glfw

class SimpleEnv:
    def __init__(self, 
                 xml_path,
                action_type='eef_pose', 
                state_type='joint_angle',
                seed = None):
        """
        args:
            xml_path: str, path to the xml file
            action_type: str, type of action space, 'eef_pose','delta_joint_angle' or 'joint_angle'
            state_type: str, type of state space, 'joint_angle' or 'ee_pose'
            seed: int, seed for random number generator
        """
        # Load the xml file
        self.env = MuJoCoParserClass(name='Tabletop',rel_xml_path=xml_path)
        self.action_type = action_type
        self.state_type = state_type
        # Arm joint names default (legacy OMY setting).
        self.joint_names = [
            'joint1',
            'joint2',
            'joint3',
            'joint4',
            'joint5',
            'joint6',
        ]
        # Auto-detect robot bindings for different robots (e.g., OMY / Nova5).
        self._configure_robot_bindings()
        self.init_viewer()
        self.reset(seed)
        # Deadband for teleop action to prevent IK jitter around zero input.
        self.action_deadband = 1e-6
        # Smooth gripper command to avoid instant jump.
        self.gripper_rate_per_step = 0.04

    def _safe_names(self, names):
        return [n for n in names if isinstance(n, str) and len(n) > 0]

    def _pick_first_available(self, candidates, name_pool):
        for c in candidates:
            if c in name_pool:
                return c
        return None

    def _configure_robot_bindings(self):
        """Auto-configure end-effector/gripper/camera names for different robot XMLs."""
        body_names = set(self._safe_names(getattr(self.env, 'body_names', [])))
        joint_names_all = self._safe_names(getattr(self.env, 'joint_names', []))
        rev_joint_names = self._safe_names(getattr(self.env, 'rev_joint_names', []))
        cam_names = set(self._safe_names(getattr(self.env, 'cam_names', [])))

        # Prefer revolute joint list if available.
        if len(rev_joint_names) > 0:
            arm = [j for j in rev_joint_names if j.startswith('joint')]
            if len(arm) >= 6:
                self.joint_names = arm[:6]
            elif len(arm) > 0:
                self.joint_names = arm
            self.gripper_joint_names = [j for j in rev_joint_names if j not in self.joint_names]
        else:
            self.gripper_joint_names = [j for j in joint_names_all if j not in self.joint_names]
        self.control_joint_names = list(self.joint_names) + list(self.gripper_joint_names)

        # End-effector body for IK / visualization / success checking.
        self.ee_body_name = self._pick_first_available(
            ['tcp_link', 'hand', 'Link6', 'right_outer_knuckle', 'left_outer_knuckle'],
            body_names,
        )
        if self.ee_body_name is None:
            self.ee_body_name = self._safe_names(getattr(self.env, 'body_names', []))[-1]

        # Gripper monitor joint for binary state & success criterion.
        self.gripper_monitor_joint = self._pick_first_available(
            ['rh_r1', 'finger_joint', 'left_inner_finger_joint', 'right_inner_finger_joint'],
            set(joint_names_all),
        )
        if self.gripper_monitor_joint is None and len(self.gripper_joint_names) > 0:
            self.gripper_monitor_joint = self.gripper_joint_names[0]
        self.gripper_open_threshold = 0.1
        # Cache per-joint limits for normalized gripper command mapping.
        self.gripper_joint_limits = {}
        for jn in self.gripper_joint_names:
            try:
                jr = self.env.model.joint(jn).range
                self.gripper_joint_limits[jn] = (float(jr[0]), float(jr[1]))
            except Exception:
                self.gripper_joint_limits[jn] = (0.0, 1.0)
        self.nova5_gripper_mode = (
            ('finger_joint' in self.gripper_joint_names)
            and ('right_outer_knuckle_joint' in self.gripper_joint_names)
        )
        self.nova5_gripper_mimic = {
            'finger_joint': 1.0,
            'left_inner_knuckle_joint': 1.0,
            'left_inner_finger_joint': -1.0,
            'right_inner_knuckle_joint': -1.0,
            'right_inner_finger_joint': 1.0,
            'right_outer_knuckle_joint': -1.0,
        }

        # Camera names with fallback.
        self.agent_cam_name = 'agentview' if 'agentview' in cam_names else None
        if self.agent_cam_name is None and len(cam_names) > 0:
            self.agent_cam_name = sorted(list(cam_names))[0]
        self.wrist_cam_name = 'egocentric' if 'egocentric' in cam_names else self.agent_cam_name
        self.side_cam_name = 'sideview' if 'sideview' in cam_names else self.agent_cam_name

    def init_viewer(self):
        '''
        Initialize the viewer
        '''
        self.env.reset()
        self.env.init_viewer(
            distance          = 2.0,
            elevation         = -30, 
            transparent       = False,
            black_sky         = True,
            use_rgb_overlay = False,
            loc_rgb_overlay = 'top right',
        )
    def reset(self, seed = None):
        '''
        Reset the environment
        Move the robot to a initial position, set the object positions based on the seed
        '''
        if seed is not None:
            np.random.seed(seed=seed)
        q_init = np.deg2rad([0,0,0,0,0,0])
        # Robot-specific home pose for safer initialization.
        if self.ee_body_name == 'Link6':
            # Nova5: keep gripper pointing down and away from objects.
            init_p = np.array([0.24, 0.0, 1.15], dtype=np.float32)
            init_rpy_deg = [180.0, 0.0, 0.0]
        else:
            # Legacy OMY home.
            init_p = np.array([0.3, 0.0, 1.0], dtype=np.float32)
            init_rpy_deg = [90.0, -0.0, 90.0]

        q_zero,ik_err_stack,ik_info = solve_ik(
            env = self.env,
            joint_names_for_ik = self.joint_names,
            body_name_trgt     = self.ee_body_name,
            q_init       = q_init, # ik from zero pose
            p_trgt       = init_p,
            R_trgt       = rpy2r(np.deg2rad(init_rpy_deg)),
        )
        self.env.forward(q=q_zero,joint_names=self.joint_names,increase_tick=False)

        # Set object positions
        obj_names = self.env.get_body_names(prefix='body_obj_')
        n_obj = len(obj_names)
        if self.ee_body_name == 'Link6':
            # Nova5: spawn objects further forward to avoid startup collision.
            x_range = [+0.48, +0.65]
            y_range = [-0.18, +0.18]
            min_dist = 0.16
        else:
            x_range = [+0.24, +0.4]
            y_range = [-0.2, +0.2]
            min_dist = 0.2
        obj_xyzs = sample_xyzs(
            n_obj,
            x_range   = x_range,
            y_range   = y_range,
            z_range   = [0.82,0.82],
            min_dist  = min_dist,
            xy_margin = 0.0
        )
        for obj_idx in range(n_obj):
            self.env.set_p_base_body(body_name=obj_names[obj_idx],p=obj_xyzs[obj_idx,:])
            self.env.set_R_base_body(body_name=obj_names[obj_idx],R=np.eye(3,3))
        self.env.forward(increase_tick=False)

        # Set the initial pose of the robot
        self.last_q = copy.deepcopy(q_zero)
        self.q = np.concatenate([q_zero, np.array([0.0] * len(self.gripper_joint_names))])
        self.p0, self.R0 = self.env.get_pR_body(body_name=self.ee_body_name)
        mug_init_pose, plate_init_pose = self.get_obj_pose()
        self.obj_init_pose = np.concatenate([mug_init_pose, plate_init_pose],dtype=np.float32)
        for _ in range(100):
            self.step_env()
        print("DONE INITIALIZATION")
        self.gripper_state = False
        self.gripper_cmd_scalar = 0.0
        self.past_chars = []

    def step(self, action):
        '''
        Take a step in the environment
        args:
            action: np.array of shape (7,), action to take
        returns:
            state: np.array, state of the environment after taking the action
                - ee_pose: [px,py,pz,r,p,y]
                - joint_angle: [j1,j2,j3,j4,j5,j6]

        '''
        if self.action_type == 'eef_pose':
            action = np.asarray(action, dtype=np.float32)
            motion = action[:6]
            has_motion = np.any(np.abs(motion) > self.action_deadband)

            # On zero motion, keep last commanded joints to avoid IK solution hopping.
            if not has_motion:
                if hasattr(self, 'compute_q'):
                    q = copy.deepcopy(self.compute_q)
                else:
                    q = self.env.get_qpos_joints(joint_names=self.joint_names)
            else:
                q = self.env.get_qpos_joints(joint_names=self.joint_names)
                self.p0 += motion[:3]
                self.R0 = self.R0.dot(rpy2r(motion[3:6]))
                q, ik_err_stack, ik_info = solve_ik(
                    env                = self.env,
                    joint_names_for_ik = self.joint_names,
                    body_name_trgt     = self.ee_body_name,
                    q_init             = q,
                    p_trgt             = self.p0,
                    R_trgt             = self.R0,
                    max_ik_tick        = 50,
                    ik_stepsize        = 1.0,
                    ik_eps             = 1e-2,
                    ik_th              = np.radians(5.0),
                    render             = False,
                    verbose_warning    = False,
                )
        elif self.action_type == 'delta_joint_angle':
            q = action[:-1] + self.last_q
        elif self.action_type == 'joint_angle':
            q = action[:-1]
        else:
            raise ValueError('action_type not recognized')
        
        # Map normalized gripper input [0,1] to each joint's physical range.
        g_target = float(np.clip(action[-1], 0.0, 1.0))
        if not hasattr(self, 'gripper_cmd_scalar'):
            self.gripper_cmd_scalar = g_target
        dg = g_target - self.gripper_cmd_scalar
        dg = np.clip(dg, -self.gripper_rate_per_step, self.gripper_rate_per_step)
        self.gripper_cmd_scalar = float(np.clip(self.gripper_cmd_scalar + dg, 0.0, 1.0))
        g = self.gripper_cmd_scalar
        gripper_cmd = []
        if self.nova5_gripper_mode and ('finger_joint' in self.gripper_joint_limits):
            f_lo, f_hi = self.gripper_joint_limits['finger_joint']
            finger_cmd = f_lo + g * (f_hi - f_lo)
            for jn in self.gripper_joint_names:
                lo, hi = self.gripper_joint_limits.get(jn, (0.0, 1.0))
                mult = self.nova5_gripper_mimic.get(jn, 1.0)
                v = float(mult * finger_cmd)
                gripper_cmd.append(float(np.clip(v, lo, hi)))
        else:
            for jn in self.gripper_joint_names:
                lo, hi = self.gripper_joint_limits.get(jn, (0.0, 1.0))
                gripper_cmd.append(lo + g * (hi - lo))
        gripper_cmd = np.array(gripper_cmd, dtype=np.float32)
        # Legacy OMY scale pattern for 4-finger setup.
        if len(self.gripper_joint_names) == 4:
            gripper_cmd[[1,3]] *= 0.8
        self.compute_q = q
        q = np.concatenate([q, gripper_cmd]) if len(gripper_cmd) > 0 else q

        self.q = q
        if self.state_type == 'joint_angle':
            return self.get_joint_state()
        elif self.state_type == 'ee_pose':
            return self.get_ee_pose()
        elif self.state_type == 'delta_q' or self.action_type == 'delta_joint_angle':
            dq =  self.get_delta_q()
            return dq
        else:
            raise ValueError('state_type not recognized')

    def step_env(self):
        # If no actuator exists (e.g. URDF-imported Nova5 scene),
        # set qpos directly and still advance one physics step.
        if getattr(self.env, 'n_ctrl', 0) <= 0:
            qpos_idxs = self.env.get_idxs_fwd(self.control_joint_names)
            qvel_idxs = self.env.get_idxs_jac(self.control_joint_names)
            # Pre-hold arm/gripper before stepping.
            self.env.data.qpos[qpos_idxs] = self.q
            self.env.data.qvel[qvel_idxs] = 0.0
            self.env.forward(
                q=self.q,
                joint_names=self.control_joint_names,
                increase_tick=False,
            )
            self.env.step(ctrl=None, increase_tick=True)
            # Post-hold again to remove one-step drift/jitter from passive dynamics.
            self.env.data.qpos[qpos_idxs] = self.q
            self.env.data.qvel[qvel_idxs] = 0.0
            self.env.forward(increase_tick=False)
        else:
            self.env.step(self.q)

    def grab_image(self):
        '''
        grab images from the environment
        returns:
            rgb_agent: np.array, rgb image from the agent's view
            rgb_ego: np.array, rgb image from the egocentric
        '''
        self.rgb_agent = self.env.get_fixed_cam_rgb(
            cam_name=self.agent_cam_name)
        self.rgb_ego = self.env.get_fixed_cam_rgb(
            cam_name=self.wrist_cam_name)
        # self.rgb_top = self.env.get_fixed_cam_rgbd_pcd(
        #     cam_name='topview')
        self.rgb_side = self.env.get_fixed_cam_rgb(
            cam_name=self.side_cam_name)
        return self.rgb_agent, self.rgb_ego
        

    def render(self, teleop=False):
        '''
        Render the environment
        '''
        self.env.plot_time()
        p_current, R_current = self.env.get_pR_body(body_name=self.ee_body_name)
        R_current = R_current @ np.array([[1,0,0],[0,0,1],[0,1,0 ]])
        self.env.plot_sphere(p=p_current, r=0.02, rgba=[0.95,0.05,0.05,0.5])
        self.env.plot_capsule(p=p_current, R=R_current, r=0.01, h=0.2, rgba=[0.05,0.95,0.05,0.5])
        rgb_egocentric_view = add_title_to_img(self.rgb_ego,text='Egocentric View',shape=(640,480))
        rgb_agent_view = add_title_to_img(self.rgb_agent,text='Agent View',shape=(640,480))
        
        self.env.viewer_rgb_overlay(rgb_agent_view,loc='top right')
        self.env.viewer_rgb_overlay(rgb_egocentric_view,loc='bottom right')
        if teleop:
            rgb_side_view = add_title_to_img(self.rgb_side,text='Side View',shape=(640,480))
            self.env.viewer_rgb_overlay(rgb_side_view, loc='top left')
            self.env.viewer_text_overlay(text1='Key Pressed',text2='%s'%(self.env.get_key_pressed_list()))
            self.env.viewer_text_overlay(text1='Key Repeated',text2='%s'%(self.env.get_key_repeated_list()))
        self.env.render()

    def get_joint_state(self):
        '''
        Get the joint state of the robot
        returns:
            q: np.array, joint angles of the robot + gripper state (0 for open, 1 for closed)
            [j1,j2,j3,j4,j5,j6,gripper]
        '''
        qpos = self.env.get_qpos_joints(joint_names=self.joint_names)
        if self.gripper_monitor_joint is not None:
            gripper = self.env.get_qpos_joint(self.gripper_monitor_joint)
            gripper_cmd = 1.0 if gripper[0] > 0.5 else 0.0
        else:
            gripper_cmd = 0.0
        return np.concatenate([qpos, [gripper_cmd]],dtype=np.float32)
    
    def teleop_robot(self):
        '''
        Teleoperate the robot using keyboard
        returns:
            action: np.array, action to take
            done: bool, True if the user wants to reset the teleoperation
        
        Keys:
            ---------     -----------------------
               w       ->        backward
            s  a  d        left   forward   right
            ---------      -----------------------
            In x, y plane

            ---------
            R: Moving Up
            F: Moving Down
            ---------
            In z axis

            ---------
            Q: Tilt left
            E: Tilt right
            UP: Look Upward
            Down: Look Donward
            Right: Turn right
            Left: Turn left
            ---------
            For rotation

            ---------
            z: reset
            SPACEBAR: gripper open/close
            ---------   


        '''
        # char = self.env.get_key_pressed()
        dpos = np.zeros(3)
        drot = np.eye(3)
        if self.env.is_key_pressed_repeat(key=glfw.KEY_S):
            dpos += np.array([0.007,0.0,0.0])
        if self.env.is_key_pressed_repeat(key=glfw.KEY_W):
            dpos += np.array([-0.007,0.0,0.0])
        if self.env.is_key_pressed_repeat(key=glfw.KEY_A):
            dpos += np.array([0.0,-0.007,0.0])
        if self.env.is_key_pressed_repeat(key=glfw.KEY_D):
            dpos += np.array([0.0,0.007,0.0])
        if self.env.is_key_pressed_repeat(key=glfw.KEY_R):
            dpos += np.array([0.0,0.0,0.007])
        if self.env.is_key_pressed_repeat(key=glfw.KEY_F):
            dpos += np.array([0.0,0.0,-0.007])
        if  self.env.is_key_pressed_repeat(key=glfw.KEY_LEFT):
            drot = rotation_matrix(angle=0.1 * 0.3, direction=[0.0, 1.0, 0.0])[:3, :3]
        if  self.env.is_key_pressed_repeat(key=glfw.KEY_RIGHT):
            drot = rotation_matrix(angle=-0.1 * 0.3, direction=[0.0, 1.0, 0.0])[:3, :3]
        if self.env.is_key_pressed_repeat(key=glfw.KEY_DOWN):
            drot = rotation_matrix(angle=0.1 * 0.3, direction=[1.0, 0.0, 0.0])[:3, :3]
        if self.env.is_key_pressed_repeat(key=glfw.KEY_UP):
            drot = rotation_matrix(angle=-0.1 * 0.3, direction=[1.0, 0.0, 0.0])[:3, :3]
        if self.env.is_key_pressed_repeat(key=glfw.KEY_Q):
            drot = rotation_matrix(angle=0.1 * 0.3, direction=[0.0, 0.0, 1.0])[:3, :3]
        if self.env.is_key_pressed_repeat(key=glfw.KEY_E):
            drot = rotation_matrix(angle=-0.1 * 0.3, direction=[0.0, 0.0, 1.0])[:3, :3]
        if self.env.is_key_pressed_once(key=glfw.KEY_Z):
            return np.zeros(7, dtype=np.float32), True
        if self.env.is_key_pressed_once(key=glfw.KEY_SPACE):
            self.gripper_state =  not  self.gripper_state
        drot = r2rpy(drot)
        action = np.concatenate([dpos, drot, np.array([self.gripper_state],dtype=np.float32)],dtype=np.float32)
        return action, False
    
    def get_delta_q(self):
        '''
        Get the delta joint angles of the robot
        returns:
            delta: np.array, delta joint angles of the robot + gripper state (0 for open, 1 for closed)
            [dj1,dj2,dj3,dj4,dj5,dj6,gripper]
        '''
        delta = self.compute_q - self.last_q
        self.last_q = copy.deepcopy(self.compute_q)
        if self.gripper_monitor_joint is not None:
            gripper = self.env.get_qpos_joint(self.gripper_monitor_joint)
            gripper_cmd = 1.0 if gripper[0] > 0.5 else 0.0
        else:
            gripper_cmd = 0.0
        return np.concatenate([delta, [gripper_cmd]],dtype=np.float32)

    def check_success(self):
        '''
        ['body_obj_mug_5', 'body_obj_plate_11']
        Check if the mug is placed on the plate
        + Gripper should be open and move upward above 0.9
        '''
        p_mug = self.env.get_p_body('body_obj_mug_5')
        p_plate = self.env.get_p_body('body_obj_plate_11')
        gripper_open = True
        if self.gripper_monitor_joint is not None:
            gripper_open = self.env.get_qpos_joint(self.gripper_monitor_joint) < self.gripper_open_threshold
        if np.linalg.norm(p_mug[:2] - p_plate[:2]) < 0.1 and np.linalg.norm(p_mug[2] - p_plate[2]) < 0.6 and gripper_open:
            p = self.env.get_p_body(self.ee_body_name)[2]
            if p > 0.9:
                return True
        return False
    
    def get_obj_pose(self):
        '''
        returns: 
            p_mug: np.array, position of the mug
            p_plate: np.array, position of the plate
        '''
        p_mug = self.env.get_p_body('body_obj_mug_5')
        p_plate = self.env.get_p_body('body_obj_plate_11')
        return p_mug, p_plate
    
    def set_obj_pose(self, p_mug, p_plate):
        '''
        Set the object poses
        args:
            p_mug: np.array, position of the mug
            p_plate: np.array, position of the plate
        '''
        self.env.set_p_base_body(body_name='body_obj_mug_5',p=p_mug)
        self.env.set_R_base_body(body_name='body_obj_mug_5',R=np.eye(3,3))
        self.env.set_p_base_body(body_name='body_obj_plate_11',p=p_plate)
        self.env.set_R_base_body(body_name='body_obj_plate_11',R=np.eye(3,3))
        self.step_env()


    def get_ee_pose(self):
        '''
        get the end effector pose of the robot + gripper state
        '''
        p, R = self.env.get_pR_body(body_name=self.ee_body_name)
        rpy = r2rpy(R)
        return np.concatenate([p, rpy],dtype=np.float32)
