from procfridge.metric import Metric
from procfridge.bluefors import parse_pressure, parse_status

class TestBlizzard:
    def test_pressure(self):
        line = r'blizzard,metric_type=pressure,path=maxigauge\ 21-10-10 pressures="CH1,        ,1, 4.30E-6,0,1,CH2,        ,1, 1.81E-2,0,1,CH3,        ,1, 5.39E+2,0,1,CH4,        ,1, 5.62E+2,0,1,CH5,        ,1, 8.55E+0,0,1,CH6,        ,1, 7.84E+0,0,1," 1633849206000000000'
        metric = Metric.from_line(line)

        out = parse_pressure(metric)

    def test_status(self):
        line = r'blizzard,metric_type=status,path=Status_21-10-10 status="tc400errorcode,0.000000E+0,tc400ovtempelec,0.000000E+0,tc400ovtemppump,0.000000E+0,tc400setspdatt,1.000000E+0,tc400pumpaccel,0.000000E+0,tc400commerr,0.000000E+0,tc400errorcode_2,0.000000E+0,tc400ovtempelec_2,0.000000E+0,tc400ovtemppump_2,0.000000E+0,tc400setspdatt_2,1.000000E+0,tc400pumpaccel_2,0.000000E+0,tc400commerr_2,0.000000E+0,ctrl_pres,1.000000E+0,cpastate,3.000000E+0,cparun,1.000000E+0,cpawarn,-0.000000E+0,cpaerr,-0.000000E+0,cpatempwi,1.859667E+1,cpatempwo,2.805445E+1,cpatempo,3.243944E+1,cpatemph,7.248722E+1,cpalp,8.713060E+1,cpalpa,8.802979E+1,cpahp,2.891180E+2,cpahpa,2.922448E+2,cpadp,2.038444E+2,cpacurrent,1.525661E+1,cpahours,1.448080E+4,cpapscale,0.000000E+0,cpatscale,1.000000E+0,cpasn,-1.483100E+4,cpamodel,1.048000E+3,cpastate_2,3.000000E+0,cparun_2,1.000000E+0,cpawarn_2,-0.000000E+0,cpaerr_2,-0.000000E+0,cpatempwi_2,1.846833E+1,cpatempwo_2,2.734833E+1,cpatempo_2,2.794889E+1,cpatemph_2,7.618333E+1,cpalp_2,7.403920E+1,cpalpa_2,7.889252E+1,cpahp_2,2.712194E+2,cpahpa_2,2.743730E+2,cpadp_2,1.986573E+2,cpacurrent_2,1.444914E+1,cpahours_2,1.449850E+4,cpapscale_2,0.000000E+0,cpatscale_2,1.000000E+0,cpasn_2,-1.482200E+4,cpamodel_2,1.048000E+3" 1633849205000000000'
        metric = Metric.from_line(line)

        out = parse_status(metric)