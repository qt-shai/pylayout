""" gcR_alld_highNA_red.py

high NA objective 0.95 (2wo=0.7um) coupling at the angle of 16.5deg
"""

import gdsfactory as gf

def gcR_alld_highNA_red (
        xin: float = 0,
        yin: float = 0,
        
        width_brdg_sprt: float = 0.075, # support width
        # width_brdg_tpr_max: float = 0.586,
        width_slb: float = 3.0, 

        width_rdg: float =0.55,

        # GC
        gc_n_periods=11, 
        gc_period=0.484, 
        gc_fill_factor=0.623, 
        gc_width_grating=0.3, 
        gc_length_taper=8,
        gc_straight_length=9.0, 
        gc_excitaion_x_lft=2.5, # before grating start
        gc_excitaion_x_offgc = 1.4, # off the first grating
        gc_excitaion_x_rght=2.0, # after grating ends
        gc_excitation_wz=0.7,

        # layers
        layer_rdg=(2, 0), 
        #layer_strp=(1, 0),
        layer_excite=(10,0), # excitation layer
        ):
    
    c = gf.Component()

    
    gc_straight_length_true = gc_straight_length - gc_fill_factor*gc_period


    xin_rect_slab  = xin
    xout_rect_slab = xin_rect_slab + gc_excitaion_x_lft + gc_excitaion_x_rght + (gc_n_periods-1) * gc_period
    y_rect_slab_min = gc_width_grating/2 + width_brdg_sprt
    y_rect_slab_max = width_slb
    brdg_dx = 0
    rect_post_tpr_top = c.add_polygon ( [(xin_rect_slab, y_rect_slab_min), 
                             (xin_rect_slab, y_rect_slab_max),
                             (xout_rect_slab, y_rect_slab_max ),
                             (xout_rect_slab,y_rect_slab_min) ], layer=layer_rdg)
    
    rect_post_tpr_btm = c.add_polygon ( [(xin_rect_slab, -y_rect_slab_min), 
                             (xin_rect_slab, -y_rect_slab_max),
                             (xout_rect_slab,-y_rect_slab_max ),
                             (xout_rect_slab,-y_rect_slab_min) ], layer=layer_rdg)
    
    comb_gc_ref = []
    
    for i in range(gc_n_periods):
        # print(i)

        gc_xin = xin_rect_slab+gc_excitaion_x_lft + i*gc_period
        gc_gap_width = round((1-gc_fill_factor)*gc_period*1E3)/1E3

        if (i==0):
            gc_clad_in_x=gc_xin
        if (i==gc_n_periods-1):
            gc_clad_out_x=gc_xin+gc_gap_width



        comb_gc_ref.append(c.add_polygon ( [(gc_xin, -gc_width_grating/2), 
                             (gc_xin+gc_gap_width, -gc_width_grating/2),
                             (gc_xin+gc_gap_width, gc_width_grating/2 ),
                             (gc_xin,gc_width_grating/2) ], layer=layer_rdg)
        )
    

    # excitation
    x_excite = gc_excitaion_x_lft + gc_excitaion_x_offgc
    e3 = c.add_ref(gf.components.ellipse(radii=(gc_excitation_wz, gc_excitation_wz), layer=layer_excite)).movex(x_excite)

    # # The big Taper - I
    # xin_tpr_slab1=xin_rect_slab - width_brdg_tpr_min - gc_length_taper
    # #w_middle = width_rdg/2+gc_width_grating/2
    # yin_tpr_slab_max1=width_rdg/2
    # yout_tpr_slab_max1=gc_width_grating/2
    
    # brdg_dx = (width_brdg_tpr_max -width_brdg_tpr_min) / 2
    # rect_post_tpr_top = c.add_polygon ( [(xin_tpr_slab1, yin_tpr_slab_max1), 
    #                          (xin_tpr_slab1+gc_length_taper, yout_tpr_slab_max1),
    #                          (xin_tpr_slab1+gc_length_taper-brdg_dx, yout_tpr_slab_max1+width_slb ),
    #                          (xin_tpr_slab1,yin_tpr_slab_max1+width_slb) ], layer=layer_rdg)
    
    # rect_post_tpr_btm = c.add_polygon ( [(xin_tpr_slab1, -yin_tpr_slab_max1), 
    #                          (xin_tpr_slab1+gc_length_taper, -yout_tpr_slab_max1),
    #                          (xin_tpr_slab1+gc_length_taper-brdg_dx, -yout_tpr_slab_max1-width_slb ),
    #                          (xin_tpr_slab1,-yin_tpr_slab_max1-width_slb) ], layer=layer_rdg)
    
    # # GC rectangles (Could be redundant):
    # gc_rect_top = c.add_polygon ( [(gc_clad_in_x, yout_tpr_slab_max1), 
    #                          (gc_clad_out_x, yout_tpr_slab_max1),
    #                          (gc_clad_out_x, yout_tpr_slab_max1+width_slb ),
    #                          (gc_clad_in_x,yout_tpr_slab_max1+width_slb) ], layer=layer_rdg)

    
    # # The big Taper - II
    # xin_tpr_slab2=xin_tpr_slab1 - width_brdg_tpr_min - gc_length_taper/2
    # yin_tpr_slab_max2=width_rdg/2
    # yout_tpr_slab_max2=w_middle/2
    
    # rect_post_tpr_top = c.add_polygon ( [(xin_tpr_slab2, yin_tpr_slab_max2), 
    #                          (xin_tpr_slab2+gc_length_taper/2, yout_tpr_slab_max2),
    #                          (xin_tpr_slab2+gc_length_taper/2-brdg_dx, yout_tpr_slab_max2+width_slb ),
    #                          (xin_tpr_slab2,yin_tpr_slab_max2+width_slb) ], layer=layer_rdg)
    
    # rect_post_tpr_btm = c.add_polygon ( [(xin_tpr_slab2, -yin_tpr_slab_max2), 
    #                          (xin_tpr_slab2+gc_length_taper/2, -yout_tpr_slab_max2),
    #                          (xin_tpr_slab2+gc_length_taper/2-brdg_dx, -yout_tpr_slab_max2-width_slb ),
    #                          (xin_tpr_slab2,-yin_tpr_slab_max2-width_slb) ], layer=layer_rdg)
    
    c.add_port(
        name="o1", center=(xin_rect_slab, 0), width=width_rdg, orientation=180, layer=layer_rdg
    )
    c.add_port(
        name="e2", center=(x_excite, 0), width=width_rdg, orientation=0, layer=layer_rdg
    )
    
    return c


if __name__ == "__main__":
    c = gf.Component()
    gcR_alld_primitive_ref = c << gcR_alld_highNA_red()
    

    c.show()  # show it in klayout
    #c.show(show_ports=True)
    

