from recon.deflectomerty.deflectometry import detect_phase, disp_from_phase, disp_from_phase_both

from unittest import TestCase
import numpy as np
import matplotlib.pyplot as plt
import muDIC as dic


def rms_diff(array1, array2):
    return np.sqrt(np.nanmean((array1 - array2)) ** 2.)

def harmonic_disp_field(disp_amp,disp_n_periodes):
    displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
    displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

    grid_undeformed = grid_grey_scales(xs, ys, grid_pitch, oversampling=oversampling, pixel_size=pixel_size)

    xs_disp = xs - displacement_x
    ys_disp = ys - displacement_y

    tol = 1.e-12
    for i in range(20):
        Xs = Xs - (xs - Xs - disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Xs / xs.max())) / (
                -1 - disp_amp * np.cos(
            disp_n_periodes * 2. * np.pi * Xs / xs.max()) / xs.max() / disp_n_periodes)
        Ys = Ys - (ys - Ys - disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Ys / ys.max())) / (
                -1 - disp_amp * np.cos(
            disp_n_periodes * 2. * np.pi * Ys / ys.max()) / ys.max() / disp_n_periodes)

        errors_x = np.max(np.abs(Xs + disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Xs / xs.max()) - xs))
        errors_y = np.max(np.abs(Ys + disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Ys / xs.max()) - ys))
        # print(errors_x)
        # print(errors_y)

        if errors_x < tol and errors_y < tol:
            print("Coordinate correction converged in %i iterations" % i)
            break

    print("Lagrange vs Eulerian correction is %f" % np.max(np.abs(xs_disp - Xs)))

    xs_disp = Xs
    ys_disp = Ys

def grid_grey_scales(xs, ys, pitch, pixel_size=1, oversampling=1):
    if np.mod(oversampling, 2) == 0:
        raise ValueError("The oversampling has to be an odd number")
    if oversampling == 1:
        coordinate_spread = np.array([0.])
    else:
        coordinate_spread = np.linspace(-pixel_size / 2., pixel_size / 2., oversampling)
    xs_spread = xs[:, :, np.newaxis, np.newaxis] + coordinate_spread[np.newaxis, np.newaxis, np.newaxis, :]
    ys_spread = ys[:, :, np.newaxis, np.newaxis] + coordinate_spread[np.newaxis, np.newaxis, :, np.newaxis]

    gray_scales = np.cos(2. * np.pi * xs_spread / float(pitch)) * np.cos(2. * np.pi * ys_spread / float(pitch))
    return np.mean(gray_scales, axis=(-1, -2))


class Test_PhaseDetection(TestCase):

    def test_rigid_body_motion_small_disp(self):

        rel_error_tol = 1e-3

        grid_pitch = 5
        n_pitches = 20

        displacement_x = 1.e-2
        displacement_y = 1.e-2

        x = np.arange(grid_pitch * n_pitches, dtype=float)
        y = np.arange(grid_pitch * n_pitches, dtype=float)

        xs, ys = np.meshgrid(x, y)

        grid_undeformed = grid_grey_scales(xs, ys, grid_pitch)

        xs_disp = xs - displacement_x
        ys_disp = ys - displacement_y

        grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch)

        phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
        phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

        disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0, grid_pitch,
                                                                    small_disp=True)

        max_rel_error_x = np.max(np.abs(disp_x_from_phase - displacement_x)) / displacement_x
        max_rel_error_y = np.max(np.abs(disp_y_from_phase - displacement_y)) / displacement_y

        if max_rel_error_x > rel_error_tol:
            self.fail("Maximum error was %f" % max_rel_error_x)
        if max_rel_error_y > rel_error_tol:
            self.fail("Maximum error was %f" % max_rel_error_y)

    def test_rigid_body_motion_large_disp(self):

        rel_error_tol = 1e-3

        grid_pitch = 5
        n_pitches = 20

        displacement_x = 1.2
        displacement_y = 1.2

        x = np.arange(grid_pitch * n_pitches, dtype=float)
        y = np.arange(grid_pitch * n_pitches, dtype=float)

        xs, ys = np.meshgrid(x, y)

        grid_undeformed = grid_grey_scales(xs, ys, grid_pitch)

        xs_disp = xs - displacement_x
        ys_disp = ys - displacement_y

        grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch)

        phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
        phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

        disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0, grid_pitch,
                                                                    small_disp=False)

        max_rel_error_x = np.max(np.abs(disp_x_from_phase - displacement_x)) / displacement_x
        max_rel_error_y = np.max(np.abs(disp_y_from_phase - displacement_y)) / displacement_y

        if max_rel_error_x > rel_error_tol:
            plt.imshow(disp_x_from_phase)
            plt.show()
            self.fail("Maximum error was %f" % max_rel_error_x)
        if max_rel_error_y > rel_error_tol:
            self.fail("Maximum error was %f" % max_rel_error_y)

    def test_sine_small_disp(self):
        acceptable_amp_loss = 0.1

        grid_pitch = 5

        disp_amp = 0.01
        disp_period = 100
        disp_n_periodes = 2

        x = np.arange(disp_n_periodes * disp_period, dtype=float)
        y = np.arange(disp_n_periodes * disp_period, dtype=float)

        xs, ys = np.meshgrid(x, y)

        displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
        displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

        grid_undeformed = grid_grey_scales(xs, ys, grid_pitch)

        xs_disp = xs - displacement_x
        ys_disp = ys - displacement_y

        grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch)

        phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
        phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

        disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0, grid_pitch,
                                                                    small_disp=True)

        peak_disp_x = np.max(np.abs(disp_x_from_phase))
        peak_disp_y = np.max(np.abs(disp_y_from_phase))

        if np.abs((peak_disp_x / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of  %f" % (1. - peak_disp_x / disp_amp))
        if np.abs((peak_disp_y / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of %f" % (1. - peak_disp_x / disp_amp))

    def test_sine_large_disp(self):
        acceptable_amp_loss = 0.05

        grid_pitch = 5
        oversampling = 15

        disp_amp = 3.57
        disp_period = 200
        disp_n_periodes = 1

        x = np.arange(disp_n_periodes * disp_period, dtype=float)
        y = np.arange(disp_n_periodes * disp_period, dtype=float)

        pixel_size = x[1] - x[0]

        xs, ys = np.meshgrid(x, y)

        displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
        displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

        grid_undeformed = grid_grey_scales(xs, ys, grid_pitch, oversampling=oversampling, pixel_size=pixel_size)

        xs_disp = xs - displacement_x
        ys_disp = ys - displacement_y

        grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch, oversampling=oversampling,
                                               pixel_size=pixel_size)

        phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
        phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

        disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0, grid_pitch,
                                                                    small_disp=True)

        disp_x_from_phase_uncor = disp_from_phase(phase_x, phase_x0, grid_pitch, small_disp=True, axis=0)

        print("Correction is %f" % np.max(np.abs(disp_x_from_phase_uncor - disp_x_from_phase)))

        plt.imshow(disp_x_from_phase)
        plt.show()

        plt.imshow(disp_x_from_phase_uncor)
        plt.show()

        plt.imshow(disp_y_from_phase)
        plt.show()

        peak_disp_x = np.max(np.abs(disp_x_from_phase))
        peak_disp_y = np.max(np.abs(disp_y_from_phase))

        if np.abs((peak_disp_x / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of  %f" % np.abs((peak_disp_x / disp_amp) - 1.))
        if np.abs((peak_disp_y / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of %f" % peak_disp_y)

    def test_half_sine_large_disp(self):
        acceptable_amp_loss = 0.1

        grid_pitch = 5
        oversampling = 9

        disp_amp = 1.7
        disp_period = 500
        disp_n_periodes = 1.0

        x = np.arange(disp_n_periodes * disp_period, dtype=float)
        y = np.arange(disp_n_periodes * disp_period, dtype=float)

        pixel_size = x[1] - x[0]

        xs, ys = np.meshgrid(x, y)

        displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
        displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

        grid_undeformed = grid_grey_scales(xs, ys, grid_pitch, oversampling=oversampling, pixel_size=pixel_size)

        xs_disp = xs - displacement_x
        ys_disp = ys - displacement_y

        grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch, oversampling=oversampling,
                                               pixel_size=pixel_size)

        phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
        phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

        # disp_y_from_phase = disp_from_phase(phase_y, phase_y0, grid_pitch, small_disp=True, axis=1)
        # disp_x_from_phase = disp_from_phase(phase_x, phase_x0, grid_pitch, small_disp=True, axis=0)

        disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0, grid_pitch,
                                                                    small_disp=False)

        plt.imshow(disp_x_from_phase)
        plt.show()

        peak_disp_x = np.max(np.abs(disp_x_from_phase))
        peak_disp_y = np.max(np.abs(disp_y_from_phase))

        if np.abs((peak_disp_x / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of  %f" % (1. - peak_disp_x / disp_amp))
        if np.abs((peak_disp_y / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of %f" % (1. - peak_disp_x / disp_amp))

    def test_phase_correction(self):
        acceptable_amp_loss = 0.02

        grid_pitch = 5
        oversampling = 15

        disp_amps = np.arange(0.1, 2.5, 0.2)
        amp = []
        amp_uncor = []
        diff = []
        for disp_amp in disp_amps:
            # disp_amp = 3.57
            disp_period = 200
            disp_n_periodes = 1

            x = np.arange(disp_n_periodes * disp_period, dtype=float)
            y = np.arange(disp_n_periodes * disp_period, dtype=float)

            pixel_size = x[1] - x[0]

            xs, ys = np.meshgrid(x, y)

            displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
            displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

            grid_undeformed = grid_grey_scales(xs, ys, grid_pitch, oversampling=oversampling, pixel_size=pixel_size)

            xs_disp = xs - displacement_x
            ys_disp = ys - displacement_y

            grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch, oversampling=oversampling,
                                                   pixel_size=pixel_size)

            phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
            phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

            # disp_x_from_phase = disp_from_phase(phase_x, phase_x0, grid_pitch, small_disp=False, axis=0)
            # disp_y_from_phase = disp_from_phase(phase_y, phase_y0, grid_pitch, small_disp=False, axis=1)

            disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0,
                                                                        grid_pitch, small_disp=False)

            disp_x_from_phase_uncor = disp_from_phase(phase_x, phase_x0, grid_pitch, small_disp=True, axis=0)

            print("Correction is %f" % np.max(np.abs(disp_x_from_phase_uncor - disp_x_from_phase)))

            # plt.imshow(disp_x_from_phase)
            # plt.show()

            # plt.imshow(disp_x_from_phase_uncor)
            # plt.show()

            # plt.imshow(disp_y_from_phase)
            # plt.show()

            peak_disp_x = np.max(np.abs(disp_x_from_phase))
            peak_disp_x_uncor = np.max(np.abs(disp_x_from_phase_uncor))
            peak_disp_y = np.max(np.abs(disp_y_from_phase))

            diff.append(np.max(np.abs(disp_x_from_phase_uncor - disp_x_from_phase)))
            amp.append(peak_disp_x)
            amp_uncor.append(peak_disp_x_uncor)

        # plt.plot(disp_amps,amp,label="corrected")
        # plt.plot(disp_amps,amp_uncor,label="uncorrected")
        # plt.twinx()
        plt.plot(disp_amps, diff, label="Corrected")
        plt.ylabel("Pixel correction [pix]")
        plt.xlabel("Displacement amplitude [pix]")
        # plt.legend(frameon=False)
        # plt.plot(disp_amps,amp_uncor,label="Uncorrected")
        plt.show()

        # if np.abs((peak_disp_x / disp_amp) - 1.) > acceptable_amp_loss:
        #     self.fail("Amplitude loss of  %f" % np.abs((peak_disp_x / disp_amp) - 1.))
        # if np.abs((peak_disp_y / disp_amp) - 1.) > acceptable_amp_loss:
        #     self.fail("Amplitude loss of %f" % peak_disp_y)

    def test_Euler_vs_Lagrange(self):
        acceptable_amp_loss = 0.1

        grid_pitch = 5
        oversampling = 9

        disp_amp = 1.
        disp_period = 500
        disp_n_periodes = 0.5

        x = np.arange(disp_n_periodes * disp_period, dtype=float)
        y = np.arange(disp_n_periodes * disp_period, dtype=float)

        pixel_size = x[1] - x[0]

        xs, ys = np.meshgrid(x, y)
        Xs, Ys = np.meshgrid(x, y)

        displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
        displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

        grid_undeformed = grid_grey_scales(xs, ys, grid_pitch, oversampling=oversampling, pixel_size=pixel_size)

        xs_disp = xs - displacement_x
        ys_disp = ys - displacement_y

        tol = 1.e-12
        for i in range(20):
            Xs = Xs - (xs - Xs - disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Xs / xs.max())) / (
                    -1 - disp_amp * np.cos(
                disp_n_periodes * 2. * np.pi * Xs / xs.max()) / xs.max() / disp_n_periodes)
            Ys = Ys - (ys - Ys - disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Ys / ys.max())) / (
                    -1 - disp_amp * np.cos(
                disp_n_periodes * 2. * np.pi * Ys / ys.max()) / ys.max() / disp_n_periodes)

            errors_x = np.max(np.abs(Xs + disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Xs / xs.max()) - xs))
            errors_y = np.max(np.abs(Ys + disp_amp * np.sin(disp_n_periodes * 2. * np.pi * Ys / xs.max()) - ys))
            # print(errors_x)
            # print(errors_y)

            if errors_x < tol and errors_y < tol:
                print("Coordinate correction converged in %i iterations" % i)
                break

        print("Lagrange vs Eulerian correction is %f" % np.max(np.abs(xs_disp - Xs)))

        xs_disp = Xs
        ys_disp = Ys

        grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch, oversampling=oversampling,
                                               pixel_size=pixel_size)

        phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
        phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

        disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0, grid_pitch,
                                                                    small_disp=False)

        plt.imshow(disp_x_from_phase)
        plt.show()

        peak_disp_x = np.max(np.abs(disp_x_from_phase))
        peak_disp_y = np.max(np.abs(disp_y_from_phase))

        if np.abs((peak_disp_x / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of  %f" % (1. - peak_disp_x / disp_amp))
        if np.abs((peak_disp_y / disp_amp) - 1.) > acceptable_amp_loss:
            self.fail("Amplitude loss of %f" % (1. - peak_disp_x / disp_amp))

    def test_bandwidth(self):

        grid_pitch = 5
        rel_error_tol = 1e-3
        peak_disp_x = []
        peak_disp_y = []
        disp_periodes = np.arange(10, 200, 10)
        for disp_period in disp_periodes:
            disp_amp = 0.01
            disp_n_periodes = 2

            x = np.arange(disp_n_periodes * disp_period, dtype=float)
            y = np.arange(disp_n_periodes * disp_period, dtype=float)

            xs, ys = np.meshgrid(x, y)

            displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
            displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

            grid_undeformed = grid_grey_scales(xs, ys, grid_pitch)

            xs_disp = xs - displacement_x
            ys_disp = ys - displacement_y

            grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch)

            phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
            phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

            disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0,
                                                                        grid_pitch,
                                                                        small_disp=False)

            peak_disp_x.append(np.max(disp_x_from_phase))
            peak_disp_y.append(np.max(disp_y_from_phase))

        peak_disp_x = np.array(peak_disp_x)
        peak_disp_y = np.array(peak_disp_y)

        plt.plot(disp_periodes, peak_disp_x / disp_amp, label="Grid pitch: %i" % grid_pitch)
        plt.xlabel("Displacement periode [pix]")
        plt.ylabel("Normalized displacement amplitude [-]")

        plt.hlines(0.9, np.min(disp_periodes), np.max(disp_periodes), linestyles="--")
        plt.legend()
        plt.show()

    def test_bandwidth_vs_grid_pitch(self):

        grid_pitches = [5, 7, 9, 11]
        for grid_pitch in grid_pitches:
            rel_error_tol = 1e-3
            peak_disp_x = []
            peak_disp_y = []
            disp_periodes = np.arange(25, 200, 10)
            for disp_period in disp_periodes:
                disp_amp = 0.01
                disp_n_periodes = 2

                x = np.arange(disp_n_periodes * disp_period, dtype=float)
                y = np.arange(disp_n_periodes * disp_period, dtype=float)

                xs, ys = np.meshgrid(x, y)

                displacement_x = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * xs / xs.max())
                displacement_y = disp_amp * np.sin(disp_n_periodes * 2. * np.pi * ys / ys.max())

                grid_undeformed = grid_grey_scales(xs, ys, grid_pitch)

                xs_disp = xs - displacement_x
                ys_disp = ys - displacement_y

                grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch)

                phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch)
                phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch)

                disp_x_from_phase, disp_y_from_phase = disp_from_phase_both(phase_x, phase_x0, phase_y, phase_y0,
                                                                            grid_pitch,
                                                                            small_disp=False)

                peak_disp_x.append(np.max(disp_x_from_phase))
                peak_disp_y.append(np.max(disp_y_from_phase))

            peak_disp_x = np.array(peak_disp_x)
            peak_disp_y = np.array(peak_disp_y)

            plt.plot(disp_periodes, peak_disp_x / disp_amp, label="Grid pitch: %i" % grid_pitch)
        plt.xlabel("Displacement periode [pix]")
        plt.ylabel("Normalized displacement amplitude [-]")
        plt.title("Bandwidth for an amplitude of %.4f pixels " % disp_amp)

        plt.hlines(0.9, np.min(disp_periodes), np.max(disp_periodes), linestyles="--")
        plt.legend(frameon=False)
        plt.show()

    def test_grid_pitch_insensitivity(self):

        # The grid pitch on the actual image is not exactly known and we need to make sure that
        # the phase detection works even when we don't hit the right value exactly.

        oversampling = 15

        rel_error_tol = 1e-3
        grid_pitch_assumed = 5.0
        grid_pitch_real = 5.05
        n_pitches = 20

        displacement_x = 1.e-2
        displacement_y = 1.e-2

        x = np.arange(grid_pitch_assumed * n_pitches, dtype=float)
        y = np.arange(grid_pitch_assumed * n_pitches, dtype=float)

        pixel_size = x[1] - x[0]

        xs, ys = np.meshgrid(x, y)

        grid_undeformed = grid_grey_scales(xs, ys, grid_pitch_real, pixel_size, oversampling)

        plt.imshow(grid_undeformed)
        plt.show()

        xs_disp = xs - displacement_x
        ys_disp = ys - displacement_y

        grid_displaced_eulr = grid_grey_scales(xs_disp, ys_disp, grid_pitch_real, pixel_size, oversampling)

        plt.imshow(grid_displaced_eulr)
        plt.show()

        phase_x, phase_y = detect_phase(grid_displaced_eulr, grid_pitch_assumed)
        phase_x0, phase_y0 = detect_phase(grid_undeformed, grid_pitch_assumed)

        disp_x_from_phase = disp_from_phase(phase_x, phase_x0, grid_pitch_assumed)
        disp_y_from_phase = disp_from_phase(phase_y, phase_y0, grid_pitch_assumed)

        plt.imshow(disp_x_from_phase)
        plt.show()

        max_rel_error_x = np.max(np.abs(disp_x_from_phase - displacement_x)) / displacement_x
        max_rel_error_y = np.max(np.abs(disp_y_from_phase - displacement_y)) / displacement_y

        if max_rel_error_x > rel_error_tol:
            self.fail("Maximum error was %f" % max_rel_error_x)
        if max_rel_error_y > rel_error_tol:
            self.fail("Maximum error was %f" % max_rel_error_y)
